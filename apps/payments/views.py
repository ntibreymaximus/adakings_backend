from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect # redirect might be for verify_payment if it leads to frontend
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status, views
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from apps.users.permissions import IsAdminOrFrontdesk, IsAdminOrSuperuser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
import requests
import hmac
import hashlib
import json # For webhook processing
import uuid # For generating references
from decimal import Decimal

from apps.orders.models import Order
from .models import Payment, PaymentTransaction
from .serializers import (
    PaymentSerializer,
    PaymentInitiateSerializer,
    PaystackWebhookSerializer,
    PaymentTransactionSerializer
)

@extend_schema(
    tags=['Payments']
)
class PaymentListAPIView(generics.ListAPIView):
    queryset = Payment.objects.all().select_related(
        'order', 
        'order__delivery_location'
    ).prefetch_related('transactions').order_by('-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrFrontdesk] # Admins and frontdesk staff can see all payments
    filterset_fields = ['status', 'payment_method', 'payment_type', 'order__order_number']
    search_fields = ['order__customer_phone', 'reference', 'paystack_reference']

    @extend_schema(
        summary="List Payments with Detailed Transaction Data",
        description="Retrieves a comprehensive list of all payments with associated PaymentTransactions, "
                    "including transaction_id, order_number, payment_method, payment_type, status, amount, "
                    "created date, and relevant customer/order information. Results are filterable by status, "
                    "method, type, and order number."
        # Tags inherited from class
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

@extend_schema(
    tags=['Payments']
)
class PaymentDetailAPIView(generics.RetrieveAPIView):
    queryset = Payment.objects.all().select_related(
        'order', 
        'order__delivery_location'
    ).prefetch_related('transactions')
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrFrontdesk]
    lookup_field = 'reference' # Use UUID reference for detail view

    @extend_schema(
        summary="Retrieve Payment Details with Transaction Data",
        description="Retrieves comprehensive details for a specific payment by its UUID reference, "
                    "including all associated PaymentTransactions and customer/order information."
        # Tags inherited from class
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PaymentInitiateAPIView(views.APIView):
    permission_classes = [IsAdminOrFrontdesk] # Only admin and frontdesk can initiate payments

    @extend_schema(
        summary="Initiate a Payment or Refund",
        request=PaymentInitiateSerializer,
        responses={
            200: OpenApiTypes.OBJECT, # For cash success or Paystack redirect URL
            201: PaymentSerializer, # For successfully created cash payment
            400: OpenApiTypes.OBJECT, # For validation errors or Paystack errors
            500: OpenApiTypes.OBJECT  # For server errors
        },
        description="Initiates a payment (Cash or Mobile Money) or a Cash Refund for an order. "
                    "For Mobile Money, returns a Paystack authorization URL. "
                    "For Cash Payment, creates the payment record directly. "
                    "For Cash Refund, creates the refund record directly.",
        tags=['Payments']
    )
    def post(self, request, *args, **kwargs):
        serializer = PaymentInitiateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        order_number = validated_data['order_number']
        amount = validated_data['amount']
        payment_method = validated_data['payment_method']
        mobile_number_raw = validated_data.get('mobile_number')
        payment_type = validated_data.get('payment_type', Payment.PAYMENT_TYPE_PAYMENT)

        order = get_object_or_404(Order, order_number=order_number)

        with transaction.atomic():
            payment_reference = uuid.uuid4()
            
            if payment_type == Payment.PAYMENT_TYPE_REFUND:
                # Check if user has permission to issue refunds (superadmin or admin only)
                if not ((request.user.is_superuser and hasattr(request.user, 'role') and request.user.role == 'superadmin') or 
                       (hasattr(request.user, 'role') and request.user.role == 'admin')):
                    return Response({"detail": "You do not have permission to issue refunds. Only superadmins and admins can process refunds."}, status=status.HTTP_403_FORBIDDEN)
                
                if payment_method not in [Payment.PAYMENT_METHOD_CASH, Payment.PAYMENT_METHOD_TELECEL_CASH, Payment.PAYMENT_METHOD_MTN_MOMO, Payment.PAYMENT_METHOD_PAYSTACK_USSD]:
                    return Response({"detail": "Only cash-type refunds are supported via this endpoint."}, status=status.HTTP_400_BAD_REQUEST)
                if amount > order.amount_paid():
                     return Response({"detail": f"Refund amount (₵{amount}) cannot exceed net amount paid (₵{order.amount_paid()})."}, status=status.HTTP_400_BAD_REQUEST)
                
                payment = Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_method=payment_method,  # Use the specified payment method
                    payment_type=Payment.PAYMENT_TYPE_REFUND,
                    status=Payment.STATUS_COMPLETED, # Cash-type refund is immediate
                    reference=payment_reference,
                    notes=f"{payment_method} refund of ₵{amount} processed by {request.user.username}."
                )
                order.save() # Recalculate order totals if necessary
                return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

            # Handling PAYMENT_TYPE_PAYMENT
            # Cash-like payments: CASH, TELECEL CASH, MTN MOMO, PAYSTACK(USSD)
            if payment_method in [Payment.PAYMENT_METHOD_CASH, Payment.PAYMENT_METHOD_TELECEL_CASH, 
                                Payment.PAYMENT_METHOD_MTN_MOMO, Payment.PAYMENT_METHOD_PAYSTACK_USSD]:
                if amount > order.balance_due() and order.balance_due() > 0:
                    # If trying to pay more than balance due, only accept up to balance_due for cash here for simplicity
                    # Or adjust to allow overpayment and let order reflect it
                    pass # Allow overpayment for cash-like payments
                
                payment = Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_method=payment_method,  # Use the specific payment method
                    payment_type=Payment.PAYMENT_TYPE_PAYMENT,
                    status=Payment.STATUS_COMPLETED,
                    reference=payment_reference,
                    notes=f"{payment_method} payment of ₵{amount} received by {request.user.username}."
                )
                
                # Update order status based on order type and current status
                if order.is_paid():  # Check if order is now fully paid
                    if order.delivery_type == 'Delivery':
                        # For delivery orders: Always move to Fulfilled when payment confirmed
                        order.status = Order.STATUS_FULFILLED
                    elif order.status == Order.STATUS_PENDING:
                        # For pickup orders: Pending -> Accepted when payment received
                        order.status = Order.STATUS_ACCEPTED
                
                order.save() # Recalculate order totals
                return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

            elif payment_method == Payment.PAYMENT_METHOD_PAYSTACK_API:
                if not mobile_number_raw:
                    return Response({"mobile_number": "Mobile number is required for mobile money."}, status=status.HTTP_400_BAD_REQUEST)
                
                # Basic Mobile Number Cleaning (adapt as per your existing logic)
                cleaned_mobile_number = mobile_number_raw.strip()
                if cleaned_mobile_number.startswith('0') and len(cleaned_mobile_number) == 10:
                    cleaned_mobile_number = '233' + cleaned_mobile_number[1:]
                elif cleaned_mobile_number.startswith('+') and cleaned_mobile_number.startswith('+233'):
                    cleaned_mobile_number = cleaned_mobile_number[1:]
                
                if not (cleaned_mobile_number.startswith('233') and len(cleaned_mobile_number) == 12 and cleaned_mobile_number[3:].isdigit()):
                    return Response({"mobile_number": "Invalid Ghanaian mobile number format (expected 233XXXXXXXXX)."}, status=status.HTTP_400_BAD_REQUEST)

                # Create a pending payment record first
                payment = Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_method=Payment.PAYMENT_METHOD_PAYSTACK_API,  # Use the specific method
                    payment_type=Payment.PAYMENT_TYPE_PAYMENT,
                    status=Payment.STATUS_PENDING, # Start as pending
                    reference=payment_reference,
                    mobile_number=cleaned_mobile_number
                )

                paystack_secret = settings.PAYSTACK_SECRET_KEY
                if not paystack_secret:
                    return Response({"detail": "Paystack secret key not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                paystack_url = "https://api.paystack.co/transaction/initialize"
                headers = {
                    "Authorization": f"Bearer {paystack_secret}",
                    "Content-Type": "application/json"
                }
                callback_url = request.build_absolute_uri(
                    reverse('payments_api:verify-payment', kwargs={'reference': str(payment.reference)})
                )
                payload_data = {
                    "email": f"customer_{order.id}_{payment.id}@example.com", # Ensure unique enough email
                    "amount": int(amount * 100), # Amount in pesewas
                    "currency": "GHS",
                    "reference": str(payment.reference),
                    "callback_url": callback_url,
                    "metadata": {
                        "order_db_id": order.id,
                        "order_number": order.order_number,
                        "payment_db_id": payment.id,
                        "customer_phone_submitted": mobile_number_raw,
                    }
                }
                try:
                    api_response = requests.post(paystack_url, headers=headers, json=payload_data, timeout=10)
                    api_response.raise_for_status() # Raise HTTPError for bad responses (4XX or 5XX)
                    response_data = api_response.json()

                    if response_data.get('status'):
                        authorization_url = response_data.get('data', {}).get('authorization_url')
                        paystack_api_reference = response_data.get('data', {}).get('reference')

                        if authorization_url and paystack_api_reference:
                            payment.paystack_reference = paystack_api_reference
                            payment.response_data = response_data
                            payment.status = Payment.STATUS_PROCESSING # Update status
                            payment.save()

                            PaymentTransaction.objects.create(
                                payment=payment,
                                transaction_id=paystack_api_reference,
                                status='initialized',
                                amount=payment.amount,
                                response_data=response_data
                            )
                            return Response({
                                'status': 'success',
                                'payment_method': 'mobile_money',
                                'authorization_url': authorization_url,
                                'payment_reference': str(payment.reference)
                            }, status=status.HTTP_200_OK)
                        else:
                            error_msg = response_data.get('message', 'Paystack init failed: No authorization URL or reference.')
                            payment.status = Payment.STATUS_FAILED
                            payment.notes = error_msg
                            payment.save()
                            return Response({"detail": error_msg}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        error_msg = response_data.get('message', 'Paystack API did not return success status.')
                        payment.status = Payment.STATUS_FAILED
                        payment.notes = error_msg
                        payment.save()
                        return Response({"detail": error_msg}, status=status.HTTP_400_BAD_REQUEST)
                
                except requests.exceptions.RequestException as e:
                    payment.status = Payment.STATUS_FAILED
                    payment.notes = f"Paystack request error: {str(e)}"
                    payment.save()
                    return Response({"detail": f"Payment processing error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"detail": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

class PaystackVerifyAPIView(views.APIView):
    permission_classes = [AllowAny] # Paystack redirects here, user might not be logged in on this browser session

    @extend_schema(
        summary="Verify Paystack Payment",
        description="Endpoint for Paystack to redirect to after a payment attempt. Verifies the transaction and updates statuses.",
        parameters=[
            OpenApiParameter(name='reference', description='The payment reference (UUID) from our system.', type=OpenApiTypes.STR, location=OpenApiParameter.PATH, required=True),
            OpenApiParameter(name='trxref', description='Transaction reference from Paystack (if provided in query)._Alternate to `reference` from Paystack._', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name='reference', description='Duplicate of `trxref` that Paystack sometimes sends._Alternate to `trxref`._', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False)
        ],
        responses={
            200: OpenApiTypes.OBJECT, # Success (can redirect to a frontend success page)
            400: OpenApiTypes.OBJECT, # Error verifying
            404: OpenApiTypes.OBJECT  # Payment not found
        },
        tags=['Payments']
    )
    def get(self, request, reference):
        payment = get_object_or_404(Payment, reference=reference)
        paystack_ref_from_query = request.query_params.get('trxref') or request.query_params.get('reference')

        # If Paystack provides its own reference in query, ensure it matches what we stored, if we stored one
        if payment.paystack_reference and paystack_ref_from_query and payment.paystack_reference != paystack_ref_from_query:
            # Log this discrepancy, but proceed with verification using our stored reference
            print(f"Warning: Paystack query ref '{paystack_ref_from_query}' differs from stored ref '{payment.paystack_reference}' for payment '{payment.reference}'")
        
        # Use the paystack_reference stored on the payment record for verification
        # This is the reference Paystack returned during initialization.
        verification_reference = payment.paystack_reference or str(payment.reference)

        paystack_secret = settings.PAYSTACK_SECRET_KEY
        if not paystack_secret:
            # Potentially redirect to a generic error page on frontend
            return Response({"detail": "Paystack secret key not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        verify_url = f"https://api.paystack.co/transaction/verify/{verification_reference}"
        headers = {"Authorization": f"Bearer {paystack_secret}"}

        try:
            api_response = requests.get(verify_url, headers=headers, timeout=10)
            api_response.raise_for_status()
            response_data = api_response.json()

            payment.response_data = response_data # Store latest response
            verified_successfully = False

            if response_data.get('status') and response_data.get('data', {}).get('status') == 'success':
                # Check amount paid matches expected amount
                amount_paid_pesewas = response_data.get('data', {}).get('amount', 0)
                if Decimal(amount_paid_pesewas / 100) == payment.amount:
                    payment.status = Payment.STATUS_COMPLETED
                    verified_successfully = True
                    
                    # Update order status based on order type and current status
                    order = payment.order
                    if order.is_paid():  # Check if order is now fully paid
                        if order.delivery_type == 'Delivery':
                            # For delivery orders: Always move to Fulfilled when payment confirmed
                            order.status = Order.STATUS_FULFILLED
                        elif order.status == Order.STATUS_PENDING:
                            # For pickup orders: Pending -> Accepted when payment received
                            order.status = Order.STATUS_ACCEPTED
                        order.save(update_fields=['status'])
                else:
                    payment.status = Payment.STATUS_FAILED
                    payment.notes = f"Amount mismatch: Expected {payment.amount}, Paystack reported {Decimal(amount_paid_pesewas/100)}."
            else:
                payment.status = Payment.STATUS_FAILED
                payment.notes = response_data.get('data', {}).get('gateway_response', 'Verification failed.')
            
            payment.save()

            # Update or create PaymentTransaction
            transaction = payment.transactions.filter(transaction_id=verification_reference).first()
            if transaction:
                transaction.status = 'success' if verified_successfully else 'failed'
                transaction.is_verified = True
                transaction.response_data = response_data
                transaction.save()
            else:
                PaymentTransaction.objects.create(
                    payment=payment,
                    transaction_id=verification_reference,
                    status='success' if verified_successfully else 'failed',
                    amount=payment.amount,
                    response_data=response_data,
                    is_verified=True
                )
            
            # Redirect to a frontend page with status
            # This should ideally be a configurable frontend URL
            frontend_redirect_url = settings.FRONTEND_ORDER_DETAIL_URL.format(order_number=payment.order.order_number)
            status_query_param = "payment_success" if verified_successfully else "payment_failed"
            return redirect(f"{frontend_redirect_url}?status={status_query_param}&ref={payment.reference}")

        except requests.exceptions.RequestException as e:
            payment.status = Payment.STATUS_FAILED
            payment.notes = f"Paystack verification error: {str(e)}"
            payment.save()
            # Redirect to a frontend error page
            frontend_redirect_url = settings.FRONTEND_ORDER_DETAIL_URL.format(order_number=payment.order.order_number)
            return redirect(f"{frontend_redirect_url}?status=payment_error&ref={payment.reference}")
        except Exception as e:
            # Generic error, log it
            payment.status = Payment.STATUS_FAILED
            payment.notes = f"Generic verification error: {str(e)}"
            payment.save()
            frontend_redirect_url = settings.FRONTEND_ORDER_DETAIL_URL.format(order_number=payment.order.order_number)
            return redirect(f"{frontend_redirect_url}?status=payment_error&ref={payment.reference}")

@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookAPIView(views.APIView):
    permission_classes = [AllowAny] # Webhooks are server-to-server

    @extend_schema(
        summary="Paystack Webhook Handler",
        request=PaystackWebhookSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
        description="Receives and processes webhook notifications from Paystack for events like charge.success.",
        tags=['Payments']
    )
    def post(self, request, *args, **kwargs):
        paystack_signature = request.headers.get('X-Paystack-Signature')
        payload = request.body

        paystack_secret = settings.PAYSTACK_SECRET_KEY
        if not paystack_secret:
            return Response({"detail": "Webhook secret not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        computed_hmac = hmac.new(paystack_secret.encode(), payload, hashlib.sha512).hexdigest()
        if not hmac.compare_digest(computed_hmac, paystack_signature):
            return Response({"detail": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_data = json.loads(payload)
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON payload"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PaystackWebhookSerializer(data=event_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        event = serializer.validated_data['event']
        data = serializer.validated_data['data']
        paystack_api_reference = data.get('reference')

        if event == 'charge.success':
            try:
                # Try to find Payment by paystack_reference first, then by our own reference as fallback
                payment = Payment.objects.filter(paystack_reference=paystack_api_reference).first() or \
                          Payment.objects.filter(reference=paystack_api_reference).first()

                if not payment:
                    print(f"Webhook: Payment with Paystack reference {paystack_api_reference} not found.")
                    return Response({"detail": "Payment not found"}, status=status.HTTP_404_NOT_FOUND) # Or 200 if Paystack needs it

                with transaction.atomic():
                    amount_paid_pesewas = data.get('amount', 0)
                    if Decimal(amount_paid_pesewas / 100) == payment.amount:
                        payment.status = Payment.STATUS_COMPLETED
                        payment.response_data = event_data # Save full webhook data
                        payment.save()

                        # Update order status based on order type and current status
                        order = payment.order
                        if order.is_paid():  # Check if order is now fully paid
                            if order.delivery_type == 'Delivery':
                                # For delivery orders: Always move to Fulfilled when payment confirmed
                                order.status = Order.STATUS_FULFILLED
                            elif order.status == Order.STATUS_PENDING:
                                # For pickup orders: Pending -> Accepted when payment received
                                order.status = Order.STATUS_ACCEPTED
                            order.save(update_fields=['status'])
                        
                        # Update/Create transaction log
                        trans_log, created = PaymentTransaction.objects.update_or_create(
                            payment=payment, 
                            transaction_id=paystack_api_reference,
                            defaults={
                                'status': 'success',
                                'amount': payment.amount,
                                'response_data': event_data,
                                'is_verified': True
                            }
                        )
                    else:
                        payment.status = Payment.STATUS_FAILED
                        payment.notes = f"Webhook amount mismatch: Expected {payment.amount}, Paystack reported {Decimal(amount_paid_pesewas/100)}."
                        payment.response_data = event_data
                        payment.save()

            except Payment.DoesNotExist:
                # This case is covered by the filter().first() check above
                pass # Already handled
            except Exception as e:
                print(f"Error processing webhook: {str(e)}") # Log error
                return Response({"detail": "Error processing event"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"status": "webhook received"}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Payments']
)
class PaymentTransactionListAPIView(generics.ListAPIView):
    """Dedicated endpoint for viewing all payment transactions with payment and order details."""
    queryset = PaymentTransaction.objects.all().select_related(
        'payment', 
        'payment__order', 
        'payment__order__delivery_location'
    ).order_by('-created_at')
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAdminOrFrontdesk]
    filterset_fields = ['status', 'is_verified', 'payment__payment_method', 'payment__status']
    search_fields = ['transaction_id', 'payment__reference', 'payment__order__order_number']
    
    @extend_schema(
        summary="List Payment Transactions",
        description="Retrieves a detailed list of all payment transactions with associated payment and order information. "
                    "Useful for transaction-level analysis and reconciliation."
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema(
    tags=['Payments']
)
class TransactionTableAPIView(views.APIView):
    """
    Provides a flattened view of all transactions for table display.
    Maps through each payment and iterates through transactions to create
    comprehensive table rows with all relevant transaction info.
    """
    permission_classes = [IsAdminOrFrontdesk]  # Admins and frontdesk staff can view transaction table
    
    @extend_schema(
        summary="Get Flattened Transaction Table Data",
        description="Returns a comprehensive list of all transactions in a flattened format suitable for table display. "
                    "Each row contains transaction_id, order_number, payment_method, payment_type, status, amount, "
                    "date, and customer details. Data is flattened from payments and their associated transactions.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "transactions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "transaction_id": {"type": "string"},
                                "order_number": {"type": "string"},
                                "payment_method": {"type": "string"},
                                "payment_type": {"type": "string"},
                                "status": {"type": "string"},
                                "amount": {"type": "number"},
                                "date": {"type": "string", "format": "date-time"},
                                "customer_phone": {"type": "string"},
                                "payment_reference": {"type": "string"},
                                "currency": {"type": "string"},
                                "is_verified": {"type": "boolean"},
                                "order_total": {"type": "number"},
                                "delivery_type": {"type": "string"}
                            }
                        }
                    },
                    "summary": {
                        "type": "object",
                        "properties": {
                            "total_transactions": {"type": "integer"},
                            "total_amount": {"type": "number"},
                            "successful_transactions": {"type": "integer"},
                            "failed_transactions": {"type": "integer"}
                        }
                    }
                }
            }
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Returns flattened transaction data for table display.
        Maps through each payment and iterates through transactions.
        """
        # Get all payments with related data
        payments = Payment.objects.select_related(
            'order', 
            'order__delivery_location'
        ).prefetch_related('transactions').order_by('-created_at')
        
        transaction_rows = []
        total_amount = Decimal('0.00')
        successful_count = 0
        failed_count = 0
        
        # Map through each payment
        for payment in payments:
            # Get basic payment/order info that will be shared across transactions
            base_row_data = {
                'order_number': payment.order.order_number,
                'payment_method': payment.get_payment_method_display(),
                'payment_type': payment.get_payment_type_display(),
                'payment_reference': str(payment.reference),
                'customer_phone': payment.order.customer_phone,
                'order_total': float(payment.order.total_price),
                'delivery_type': payment.order.delivery_type,
            }
            
            # Iterate through transactions for this payment
            transactions = payment.transactions.all()
            
            if transactions.exists():
                # If payment has transactions, create a row for each transaction
                for transaction in transactions:
                    row = base_row_data.copy()
                    row.update({
                        'transaction_id': transaction.transaction_id,
                        'status': transaction.get_status_display(),
                        'amount': float(transaction.amount),
                        'date': transaction.created_at.isoformat(),
                        'currency': transaction.currency,
                        'is_verified': transaction.is_verified,
                    })
                    transaction_rows.append(row)
                    total_amount += transaction.amount
                    
                    if transaction.status == 'success':
                        successful_count += 1
                    elif transaction.status == 'failed':
                        failed_count += 1
            else:
                # If payment has no transactions, create a row with payment data
                row = base_row_data.copy()
                row.update({
                    'transaction_id': f"PAY-{payment.id}",  # Generate ID for payments without transactions
                    'status': payment.get_status_display(),
                    'amount': float(payment.amount),
                    'date': payment.created_at.isoformat(),
                    'currency': 'GHS',  # Default currency
                    'is_verified': payment.status == Payment.STATUS_COMPLETED,
                })
                transaction_rows.append(row)
                total_amount += payment.amount
                
                if payment.status == Payment.STATUS_COMPLETED:
                    successful_count += 1
                elif payment.status == Payment.STATUS_FAILED:
                    failed_count += 1
        
        # Create summary data
        summary = {
            'total_transactions': len(transaction_rows),
            'total_amount': float(total_amount),
            'successful_transactions': successful_count,
            'failed_transactions': failed_count
        }
        
        return Response({
            'transactions': transaction_rows,
            'summary': summary
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Payments']
)
class PaymentModesAPIView(views.APIView):
    permission_classes = [IsAdminOrFrontdesk]  # Only admin and frontdesk can access payment modes
    
    @extend_schema(
        summary="List Payment Modes",
        description="Returns the available payment modes that can be used when processing payments.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "payment_modes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "string"},
                                "label": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Returns the available payment modes/methods.
        """
        payment_modes = [
            {"value": "CASH", "label": "Cash", "disabled": False},
            {"value": "TELECEL CASH", "label": "Telecel Cash", "disabled": False},
            {"value": "MTN MOMO", "label": "MTN MoMo", "disabled": False},
            {"value": "PAYSTACK(USSD)", "label": "Paystack (USSD)", "disabled": False},
            {"value": "PAYSTACK(API)", "label": "Paystack (API) - Coming Soon", "disabled": True}
        ]
        
        return Response({"payment_modes": payment_modes}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Payment History",
    description="Returns a comprehensive payment history with detailed transaction information, including order details, payment methods, and transaction timelines.",
    parameters=[
        OpenApiParameter(
            name='order_number',
            description='Filter by specific order number',
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name='payment_method',
            description='Filter by payment method (CASH, TELECEL CASH, MTN MOMO, etc.)',
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name='status',
            description='Filter by payment status (pending, completed, failed, etc.)',
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name='days',
            description='Number of days to look back (default: 30)',
            required=False,
            type=OpenApiTypes.INT
        ),
    ],
    tags=['Payments']
)
class PaymentHistoryAPIView(views.APIView):
    permission_classes = [IsAdminOrFrontdesk]
    
    def get(self, request, *args, **kwargs):
        """
        Returns comprehensive payment history with filtering options.
        """
        # Start with all payments
        queryset = Payment.objects.select_related(
            'order', 
            'order__delivery_location'
        ).prefetch_related('transactions').order_by('-created_at')
        
        # Apply filters
        order_number = request.query_params.get('order_number')
        if order_number:
            queryset = queryset.filter(order__order_number__icontains=order_number)
        
        payment_method = request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method__icontains=payment_method)
        
        payment_status = request.query_params.get('status')
        if payment_status:
            queryset = queryset.filter(status__icontains=payment_status)
        
        # Filter by days (default to 30 days)
        days = request.query_params.get('days', '30')
        try:
            days_int = int(days)
            from django.utils import timezone
            cutoff_date = timezone.now() - timezone.timedelta(days=days_int)
            queryset = queryset.filter(created_at__gte=cutoff_date)
        except ValueError:
            pass  # Invalid days parameter, ignore filter
        
        payment_history = []
        for payment in queryset:
            # Get transactions for this payment
            transactions = payment.transactions.all().order_by('created_at')
            
            transaction_details = []
            for transaction in transactions:
                transaction_details.append({
                    'transaction_id': transaction.transaction_id,
                    'status': transaction.get_status_display(),
                    'amount': float(transaction.amount),
                    'currency': transaction.currency,
                    'is_verified': transaction.is_verified,
                    'created_at': transaction.created_at.isoformat(),
                    'time_ago': transaction.time_ago(),
                })
            
            # Create payment history entry
            history_entry = {
                'payment_id': payment.id,
                'payment_reference': str(payment.reference),
                'order_number': payment.order.order_number,
                'customer_phone': payment.order.customer_phone,
                'payment_method': payment.get_payment_method_display(),
                'payment_type': payment.get_payment_type_display(),
                'status': payment.get_status_display(),
                'amount': float(payment.amount),
                'order_total': float(payment.order.total_price),
                'delivery_type': payment.order.delivery_type,
                'delivery_location': payment.order.delivery_location.name if payment.order.delivery_location else None,
                'paystack_reference': payment.paystack_reference,
                'mobile_number': payment.mobile_number,
                'notes': payment.notes,
                'created_at': payment.created_at.isoformat(),
                'updated_at': payment.updated_at.isoformat(),
                'time_ago': payment.time_ago(),
                'transactions': transaction_details,
                'transaction_count': len(transaction_details),
                'payment_timeline': [
                    {
                        'event': 'Payment Created',
                        'status': 'pending',
                        'timestamp': payment.created_at.isoformat(),
                        'is_current': payment.status == Payment.STATUS_PENDING
                    },
                    {
                        'event': f'Payment {payment.get_status_display()}',
                        'status': payment.status,
                        'timestamp': payment.updated_at.isoformat(),
                        'is_current': True
                    }
                ]
            }
            payment_history.append(history_entry)
        
        # Generate summary statistics
        total_payments = len(payment_history)
        total_amount = sum(entry['amount'] for entry in payment_history)
        completed_payments = [entry for entry in payment_history if entry['status'] == 'Completed']
        failed_payments = [entry for entry in payment_history if entry['status'] == 'Failed']
        pending_payments = [entry for entry in payment_history if entry['status'] in ['Pending', 'Processing']]
        
        summary = {
            'total_payments': total_payments,
            'total_amount': total_amount,
            'completed_count': len(completed_payments),
            'completed_amount': sum(entry['amount'] for entry in completed_payments),
            'failed_count': len(failed_payments),
            'failed_amount': sum(entry['amount'] for entry in failed_payments),
            'pending_count': len(pending_payments),
            'pending_amount': sum(entry['amount'] for entry in pending_payments),
        }
        
        return Response({
            'count': total_payments,
            'summary': summary,
            'results': payment_history
        }, status=status.HTTP_200_OK)
