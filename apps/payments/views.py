from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, DetailView, TemplateView, View, ListView
from django.views.generic.edit import FormMixin
from django.conf import settings
from django.utils.decorators import method_decorator
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from datetime import datetime, timedelta
from django.views.decorators.csrf import ensure_csrf_cookie # For AJAX CSRF
from .models import Payment, PaymentTransaction
from apps.orders.models import Order
from .forms import PaymentForm # PaystackPaymentForm removed as MobilePaymentView is removed
import requests
import json
import uuid
import hmac
import hashlib
from decimal import Decimal, InvalidOperation # Added InvalidOperation


class PaymentMethodSelectionView(LoginRequiredMixin, FormView):
    """View for selecting payment method"""
    template_name = 'payments/process_payment.html'
    form_class = PaymentForm
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        order_identifier = kwargs.get('order_number') # Changed from order_id
        self.order = get_object_or_404(Order, order_number=order_identifier) # Changed to lookup by order_number
    
    def get_form_kwargs(self):
        """Pass the order to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.order
        kwargs['step'] = 'select_method'  # First step - selecting payment method
        return kwargs
        
    def get_initial(self):
        """Set initial form values."""
        initial = {
            'amount': self.order.total_price,
            'payment_method': Payment.PAYMENT_METHOD_CASH,  # Default to cash
        }
        return initial
    
    def get_context_data(self, **kwargs):
        """Add order to the template context."""
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        context['order_customer_phone'] = self.order.customer_phone # For pre-filling mobile number
        
        # Add form errors to context for debugging
        form = context.get('form')
        if form and not form.is_valid() and self.request.method == 'POST':
            context['form_errors'] = form.errors
            
            # Add non-field errors
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(self.request, f"Error: {error}")
            
            # Add field-specific errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"Error in {field}: {error}")
        
        return context
    
    def get_success_url(self):
        """Determine success URL based on payment method."""
        payment = getattr(self, 'payment', None)
        if not payment:
            return reverse('orders:order_detail', kwargs={'order_number': self.order.order_number}) # Changed pk to order_number
            
        if payment.payment_method == Payment.PAYMENT_METHOD_CASH:
            url = reverse('payments:cash_payment', kwargs={'payment_id': payment.id})
            return url
        elif payment.payment_method == Payment.PAYMENT_METHOD_MOBILE:
            url = reverse('payments:mobile_payment', kwargs={'payment_id': payment.id})
            return url
            
        url = reverse('orders:order_detail', kwargs={'order_number': self.order.order_number}) # Changed pk to order_number
        return url
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Error in {field}: {error}")
        
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """Process the valid form."""
        is_ajax = self.request.headers.get('x-requested-with') == 'XMLHttpRequest'

        payment = form.save(commit=False)
        payment.order = self.order # Ensure order is linked
        if not payment.reference:
            payment.reference = str(uuid.uuid4())

        if is_ajax:
            try:
                if payment.payment_method == Payment.PAYMENT_METHOD_CASH:
                    payment.status = Payment.STATUS_COMPLETED
                    payment.save()
                    
                    order = payment.order
                    if order.status == 'Pending':
                        order.status = 'Accepted'  # Mark as Accepted after payment
                        order.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Cash payment recorded successfully.',
                        'payment_id': payment.id,
                        'order_number': order.order_number,
                        'payment_method': 'cash',
                        'amount': payment.amount,
                        'payment_status': payment.status
                    })

                elif payment.payment_method == Payment.PAYMENT_METHOD_MOBILE:
                    mobile_number = self.request.POST.get('mobile_number')
                    
                    # Basic validation for mobile_number
                    if not mobile_number or not mobile_number.strip(): # TODO: Adapt more robust validation from PaystackPaymentForm
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Valid mobile number is required for mobile payment.'
                        }, status=400)
                    
                    # Clean phone number (simple version, can be expanded)
                    cleaned_mobile_number = mobile_number.strip()
                    if cleaned_mobile_number.startswith('+'):
                        cleaned_mobile_number = cleaned_mobile_number[1:]
                    if cleaned_mobile_number.startswith('0'):
                         cleaned_mobile_number = '233' + cleaned_mobile_number[1:]
                    
                    if not (cleaned_mobile_number.startswith('233') and len(cleaned_mobile_number) == 12 and cleaned_mobile_number[3:].isdigit()):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid Ghanaian mobile number format. Expected 0XXXXXXXXX or +233XXXXXXXXX.'
                        }, status=400)

                    payment.mobile_number = cleaned_mobile_number
                    payment.status = Payment.STATUS_PROCESSING
                    payment.save() # Save once to get ID if new, and to store mobile number

                    paystack_secret = settings.PAYSTACK_SECRET_KEY
                    paystack_url = "https://api.paystack.co/transaction/initialize"
                    headers = {
                        "Authorization": f"Bearer {paystack_secret}",
                        "Content-Type": "application/json"
                    }
                    callback_url = self.request.build_absolute_uri(
                        reverse('payments:verify_payment', kwargs={'reference': str(payment.reference)})
                    )
                    payload_data = {
                        "email": f"customer_{self.order.customer_phone.replace('+', '').replace(' ', '')}@example.com",
                        "amount": int(payment.amount * 100), # Paystack expects amount in kobo/pesewas
                        "currency": "GHS",
                        "reference": str(payment.reference),
                        "callback_url": callback_url,
                        "metadata": {
                            "order_id": self.order.id,
                            "payment_id": payment.id,
                            "custom_fields": [{
                                "display_name": "Phone Number",
                                "variable_name": "phone_number",
                                "value": payment.mobile_number 
                            }]
                        }
                    }

                    try:
                        response = requests.post(paystack_url, headers=headers, json=payload_data, timeout=10)
                        response_data = response.json()

                        if response.status_code == 200 and response_data.get('status'):
                            authorization_url = response_data.get('data', {}).get('authorization_url')
                            if authorization_url:
                                PaymentTransaction.objects.create(
                                    payment=payment,
                                    transaction_id=response_data.get('data', {}).get('reference', str(uuid.uuid4())), # Ensure a fallback for transaction_id
                                    status='initialized',
                                    amount=payment.amount,
                                    response_data=response_data
                                )
                                payment.paystack_reference = response_data.get('data', {}).get('reference', '')
                                payment.response_data = response_data
                                payment.save()
                                return JsonResponse({
                                    'status': 'success',
                                    'payment_method': 'mobile_money',
                                    'authorization_url': authorization_url,
                                    'payment_id': payment.id,
                                    'reference': str(payment.reference)
                                })
                            else:
                                payment.status = Payment.STATUS_FAILED
                                payment.save()
                                return JsonResponse({
                                    'status': 'error',
                                    'message': response_data.get('message', 'Paystack initialization failed: No authorization URL.')
                                }, status=400)
                        else:
                            payment.status = Payment.STATUS_FAILED
                            payment.save()
                            return JsonResponse({
                                'status': 'error',
                                'message': f"Paystack API error: {response_data.get('message', 'Unknown error')}"
                            }, status=response.status_code or 400)

                    except requests.exceptions.RequestException as e:
                        payment.status = Payment.STATUS_FAILED
                        payment.save()
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Payment processing error: {str(e)}'
                        }, status=500)
                
                else: # Should not happen if form is properly validated for choices
                    return JsonResponse({'status': 'error', 'message': 'Invalid payment method.'}, status=400)

            except Exception as e: # Catch any other unexpected error during AJAX processing
                # Log the error e for server-side debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"AJAX Payment Processing Error: {str(e)}", exc_info=True)
                return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}, status=500)
        else: # Not an AJAX request, process directly
            payment = form.save(commit=False)
            payment.order = self.order
            if not payment.reference:
                payment.reference = str(uuid.uuid4())

            # Handle Cash Payments Directly
            if payment.payment_method == Payment.PAYMENT_METHOD_CASH:
                payment.status = Payment.STATUS_COMPLETED
                payment.save()
                
                order = payment.order
                if order.status == "Pending": 
                    order.status = "Accepted" 
                    order.save()
                
                messages.success(self.request, 'Cash payment recorded successfully!')
                return redirect(reverse('orders:order_detail', kwargs={'order_number': self.order.order_number})) # Changed pk to order_number

            # Handle Mobile Money Payments Directly
            elif payment.payment_method == Payment.PAYMENT_METHOD_MOBILE:
                mobile_number_raw = self.request.POST.get('mobile_number')
                
                if not mobile_number_raw or not mobile_number_raw.strip():
                    # form.add_error('mobile_number', 'Valid mobile number is required for mobile payment.') # Field doesn't exist on form
                    messages.error(self.request, 'Valid mobile number is required for mobile payment.')
                    return self.form_invalid(form)

                cleaned_mobile_number = mobile_number_raw.strip()
                if cleaned_mobile_number.startswith('+'):
                    cleaned_mobile_number = cleaned_mobile_number[1:]
                if cleaned_mobile_number.startswith('0'):
                    cleaned_mobile_number = '233' + cleaned_mobile_number[1:]
                
                if not (cleaned_mobile_number.startswith('233') and len(cleaned_mobile_number) == 12 and cleaned_mobile_number[3:].isdigit()):
                    # form.add_error('mobile_number', 'Invalid Ghanaian mobile number format. Expected 0XXXXXXXXX or +233XXXXXXXXX.') # Field doesn't exist on form
                    messages.error(self.request, 'Invalid Ghanaian mobile number format.')
                    return self.form_invalid(form)

                payment.mobile_number = cleaned_mobile_number
                payment.status = Payment.STATUS_PROCESSING
                payment.save() 

                paystack_secret = settings.PAYSTACK_SECRET_KEY
                paystack_url = "https://api.paystack.co/transaction/initialize"
                headers = {
                    "Authorization": f"Bearer {paystack_secret}",
                    "Content-Type": "application/json"
                }
                callback_url = self.request.build_absolute_uri(
                    reverse('payments:verify_payment', kwargs={'reference': str(payment.reference)})
                )
                payload_data = {
                    "email": f"customer_{self.order.customer_phone.replace('+', '').replace(' ', '')}@example.com",
                    "amount": int(payment.amount * 100),
                    "currency": "GHS",
                    "reference": str(payment.reference),
                    "callback_url": callback_url,
                    "metadata": {
                        "order_id": self.order.id,
                        "payment_id": payment.id,
                        "custom_fields": [{"display_name": "Phone Number", "variable_name": "phone_number", "value": payment.mobile_number}]
                    }
                }

                try:
                    response = requests.post(paystack_url, headers=headers, json=payload_data, timeout=10)
                    response_data = response.json()

                    if response.status_code == 200 and response_data.get('status'):
                        authorization_url = response_data.get('data', {}).get('authorization_url')
                        if authorization_url:
                            PaymentTransaction.objects.create(
                                payment=payment,
                                transaction_id=response_data.get('data', {}).get('reference', str(uuid.uuid4())),
                                status='initialized',
                                amount=payment.amount,
                                response_data=response_data
                            )
                            payment.paystack_reference = response_data.get('data', {}).get('reference', '')
                            payment.response_data = response_data
                            payment.save()
                            return redirect(authorization_url)
                        else:
                            payment.status = Payment.STATUS_FAILED
                            payment.save()
                            messages.error(self.request, response_data.get('message', 'Paystack initialization failed: No authorization URL.'))
                            return redirect(reverse('payments:payment_failed')) # Consider passing payment_id or order_id if failed page needs it
                    else:
                        payment.status = Payment.STATUS_FAILED
                        payment.save()
                        messages.error(self.request, f"Paystack API error: {response_data.get('message', 'Unknown error')}")
                        return redirect(reverse('payments:payment_failed'))
                except requests.exceptions.RequestException as e:
                    payment.status = Payment.STATUS_FAILED
                    payment.save()
                    messages.error(self.request, f'Payment processing error: {str(e)}')
                    return redirect(reverse('payments:payment_failed'))
            
            else: # Should not happen with current form choices
                messages.error(self.request, "Invalid payment method selected.")
                return self.form_invalid(form)

# class CashPaymentView(LoginRequiredMixin, DetailView):
#     """View for processing cash payments"""
#     model = Payment
#     template_name = 'payments/cash_payment.html'
#     context_object_name = 'payment'
#     pk_url_kwarg = 'payment_id'
#     
#     def get_queryset(self):
#         return super().get_queryset().filter(payment_method=Payment.PAYMENT_METHOD_CASH)
#     
#     @transaction.atomic
#     def post(self, request, *args, **kwargs):
#         payment = self.get_object()
#         order = payment.order
#         
#         # Process cash payment
#         payment.status = Payment.STATUS_COMPLETED
#         payment.save()
#         
#         # Update order status
#         if order.status == 'Pending':
#             order.status = 'Confirmed'
#             order.save()
#         
#         messages.success(request, 'Cash payment recorded successfully!')
#         return redirect('orders:order_detail', pk=order.id)


# class MobilePaymentView(LoginRequiredMixin, FormView):
#     """View for initiating mobile payments via Paystack"""
#     template_name = 'payments/mobile_payment.html'
#     form_class = PaystackPaymentForm # This form is also now potentially redundant
#     
#     def setup(self, request, *args, **kwargs):
#         super().setup(request, *args, **kwargs)
#         self.payment = get_object_or_404(
#             Payment, 
#             id=kwargs.get('payment_id'),
#             payment_method=Payment.PAYMENT_METHOD_MOBILE
#         )
#     
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['payment'] = self.payment
#         context['order'] = self.payment.order
#         return context
#     
#     def form_valid(self, form):
#         payment = self.payment
#         order = payment.order
#         mobile_number = form.cleaned_data['phone_number']
#         
#         # Save mobile number to payment
#         payment.mobile_number = mobile_number
#         payment.status = Payment.STATUS_PROCESSING
#         payment.save()
#         
#         # Prepare Paystack API call
#         paystack_secret = settings.PAYSTACK_SECRET_KEY
#         url = "https://api.paystack.co/transaction/initialize"
#         
#         headers = {
#             "Authorization": f"Bearer {paystack_secret}",
#             "Content-Type": "application/json"
#         }
#         
#         callback_url = self.request.build_absolute_uri(
#             reverse('payments:verify_payment', kwargs={'reference': payment.reference})
#         )
#         
#         data = {
#             "email": f"customer_{order.customer_phone.replace('+', '').replace(' ', '')}@example.com",  # Generate email from customer phone
#             "amount": int(payment.amount * 100),  # Convert to pesewas (or lowest currency unit)
#             "currency": "GHS",
#             "reference": str(payment.reference),
#             "callback_url": callback_url,
#             "metadata": {
#                 "order_id": order.id,
#                 "payment_id": payment.id,
#                 "custom_fields": [
#                     {
#                         "display_name": "Phone Number",
#                         "variable_name": "phone_number",
#                         "value": mobile_number
#                     }
#                 ]
#             }
#         }
#         
#         try:
#             response = requests.post(url, headers=headers, json=data)
#             response_data = response.json()
#             
#             if response.status_code == 200 and response_data.get('status'):
#                 # Create transaction record
#                 transaction = PaymentTransaction.objects.create(
#                     payment=payment,
#                     transaction_id=response_data.get('data', {}).get('reference', ''),
#                     status='initialized',
#                     amount=payment.amount,
#                     response_data=response_data
#                 )
#                 
#                 # Update payment with Paystack reference
#                 payment.paystack_reference = response_data.get('data', {}).get('reference', '')
#                 payment.response_data = response_data
#                 payment.save()
#                 
#                 # Redirect to Paystack payment URL
#                 authorization_url = response_data.get('data', {}).get('authorization_url')
#                 if authorization_url:
#                     return redirect(authorization_url)
#                 else:
#                     messages.error(self.request, "Payment initialization failed. Please try again.")
#             else:
#                 messages.error(self.request, f"Payment failed: {response_data.get('message', 'Unknown error')}")
#                 payment.status = Payment.STATUS_FAILED
#                 payment.save()
#         except Exception as e:
#             messages.error(self.request, f"Payment processing error: {str(e)}")
#             payment.status = Payment.STATUS_FAILED
#             payment.save()
#         
#         return redirect('payments:payment_failed')


class VerifyPaymentView(LoginRequiredMixin, View):
    """View to verify a payment after Paystack redirect"""
    
    def get(self, request, reference):
        payment = get_object_or_404(Payment, reference=reference)
        
        # Verify payment with Paystack
        verified = self.verify_with_paystack(payment)
        
        if verified:
            # Payment verified
            payment.status = Payment.STATUS_COMPLETED
            payment.save()
            
            order = payment.order # Ensure order is defined for context
            # Update order status
            if order.status == "Pending": 
                order.status = "Accepted" 
                order.save()
            
            # Update transaction status
            pay_transaction = payment.transactions.first()
            if pay_transaction:
                pay_transaction.is_verified = True
                pay_transaction.status = 'success' # Or match Paystack's status string if different
                pay_transaction.response_data = payment.response_data # Ensure latest response data is captured if updated by verify_with_paystack
                pay_transaction.save()
            
            messages.success(request, 'Payment verified successfully!')
            order_detail_url = reverse('orders:order_detail', kwargs={'order_number': payment.order.order_number}) # Changed pk to order_number
            return redirect(f"{order_detail_url}?payment_status=success&payment_ref={payment.reference}")
        else:
            payment.status = Payment.STATUS_FAILED
            payment.save()
            
            order = payment.order # Define order for context
            # Update transaction status
            pay_transaction = payment.transactions.first()
            if pay_transaction:
                pay_transaction.status = 'failed' # Or match Paystack's status string
                pay_transaction.response_data = payment.response_data
                pay_transaction.save()
            
            messages.error(request, 'Payment verification failed.')
            order_detail_url = reverse('orders:order_detail', kwargs={'order_number': payment.order.order_number}) # Changed pk to order_number
            return redirect(f"{order_detail_url}?payment_status=failed&payment_ref={payment.reference}")
    
    def verify_with_paystack(self, payment):
        """Verify payment with Paystack API"""
        paystack_secret = settings.PAYSTACK_SECRET_KEY
        reference = payment.paystack_reference or str(payment.reference)
        
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {paystack_secret}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                # Store verification response
                payment.response_data = response_data
                payment.save()
                
                # Check if payment is successful
                if response_data.get('status') and response_data.get('data', {}).get('status') == 'success':
                    return True
            
            return False
        except Exception as e:
            # Log the error
            print(f"Paystack verification error: {str(e)}")
            return False


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(View):
    """Webhook handler for Paystack payment notifications"""
    
    def post(self, request, *args, **kwargs):
        # Get the signature header
        paystack_signature = request.headers.get('X-Paystack-Signature')
        
        if not paystack_signature:
            return HttpResponseBadRequest("No signature header")
        
        # Get request body
        payload = request.body
        
        # Verify signature
        if not self.verify_webhook_signature(payload, paystack_signature):
            return HttpResponseBadRequest("Invalid signature")
        
        # Process the webhook
        try:
            event_data = json.loads(payload)
            event = event_data.get('event')
            data = event_data.get('data', {})
            reference = data.get('reference')
            
            if event == 'charge.success':
                # Find the payment
                try:
                    payment = Payment.objects.get(paystack_reference=reference)
                    
                    # Update payment status
                    payment.status = Payment.STATUS_COMPLETED
                    payment.response_data = event_data
                    payment.save()
                    
                    # Update transaction
                    transaction = PaymentTransaction.objects.filter(payment=payment).first()
                    if transaction:
                        transaction.status = 'success'
                        transaction.is_verified = True
                        transaction.response_data = event_data
                        transaction.save()
                    
                    # Update order status
                    order = payment.order
                    if order.status == 'Pending':
                        order.status = 'Confirmed'
                        order.save()
                except Payment.DoesNotExist:
                    # Log that we couldn't find the payment
                    print(f"Payment with reference {reference} not found")
            
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")
        except Exception as e:
            # Log the error
            print(f"Webhook processing error: {str(e)}")
            return HttpResponse(status=500)
    
    def verify_webhook_signature(self, payload, signature):
        """Verify that the webhook is from Paystack"""
        paystack_secret = settings.PAYSTACK_SECRET_KEY
        
        computed_hmac = hmac.new(
            key=paystack_secret.encode(),
            msg=payload,
            digestmod=hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_hmac, signature)


class TransactionListView(LoginRequiredMixin, ListView):
    """
    View for listing all payment transactions with filtering and pagination
    """
    model = Payment
    template_name = 'payments/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 15
    
    def dispatch(self, request, *args, **kwargs):
        """Only allow admin and frontdesk staff to access"""
        if not (request.user.is_admin() or request.user.is_frontdesk()):
            messages.error(request, "You don't have permission to view transaction history.")
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter transactions based on query parameters"""
        queryset = Payment.objects.all().select_related('order').order_by('-created_at')
        
        # Filter by payment method
        payment_method = self.request.GET.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=start_date)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                # Add one day to include the end date in the range
                end_date = end_date + timedelta(days=1)
                queryset = queryset.filter(created_at__date__lt=end_date)
            except ValueError:
                pass
        
        # Search by customer name or order ID
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(order__customer_name__icontains=search_query) |
                Q(order__id__icontains=search_query) |
                Q(reference__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter choices and statistics to context"""
        context = super().get_context_data(**kwargs)
        
        # Add payment method choices
        context['payment_method_choices'] = Payment.PAYMENT_METHOD_CHOICES
        
        # Add status choices
        context['status_choices'] = Payment.PAYMENT_STATUS_CHOICES
        
        # Add current filters to context
        context['current_filters'] = {
            'payment_method': self.request.GET.get('payment_method', ''),
            'status': self.request.GET.get('status', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
            'q': self.request.GET.get('q', '')
        }
        
        # Calculate total amount for filtered transactions
        total_amount = sum(transaction.amount for transaction in context['transactions'])
        context['total_amount'] = total_amount
        
        # Calculate transaction counts by status
        queryset = self.get_queryset()
        context['transaction_counts'] = {
            'total': queryset.count(),
            'completed': queryset.filter(status=Payment.STATUS_COMPLETED).count(),
            'pending': queryset.filter(status=Payment.STATUS_PENDING).count(),
            'failed': queryset.filter(status=Payment.STATUS_FAILED).count(),
            'processing': queryset.filter(status=Payment.STATUS_PROCESSING).count(),
        }
        
        return context


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProcessCashRefundModalView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order_number_str = request.POST.get('order_number')
        refund_amount_str = request.POST.get('refund_amount')

        if not order_number_str:
            return JsonResponse({'status': 'error', 'message': 'Order Number is required.'}, status=400)
        if not refund_amount_str:
            return JsonResponse({'status': 'error', 'message': 'Refund amount is required.'}, status=400)

        try:
            order = get_object_or_404(Order, order_number=order_number_str)
        except Order.DoesNotExist: # Should be caught by get_object_or_404
            return JsonResponse({'status': 'error', 'message': 'Order not found for the given Order Number.'}, status=404)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid Order Number format.'}, status=400)

        try:
            refund_amount = Decimal(refund_amount_str)
            if refund_amount <= Decimal('0.00'):
                return JsonResponse({'status': 'error', 'message': 'Refund amount must be positive.'}, status=400)
        except InvalidOperation:
            return JsonResponse({'status': 'error', 'message': 'Invalid refund amount format.'}, status=400)

        current_amount_paid_net = order.amount_paid() # Net amount after previous refunds
        if refund_amount > current_amount_paid_net:
            return JsonResponse({'status': 'error', 'message': f'Refund amount (₵{refund_amount}) cannot exceed the net amount paid (₵{current_amount_paid_net}).'}, status=400)

        try:
            with transaction.atomic():
                Payment.objects.create(
                    order=order,
                    amount=refund_amount,
                    payment_method=Payment.PAYMENT_METHOD_CASH,
                    payment_type=Payment.PAYMENT_TYPE_REFUND,
                    status=Payment.STATUS_COMPLETED, # Cash refund is immediate
                    reference=uuid.uuid4(),
                    notes=f"Cash refund of ₵{refund_amount} processed by {request.user.username or 'system'}."
                )
                order.refresh_from_db() 
            return JsonResponse({'status': 'success', 'message': f'Cash refund of ₵{refund_amount} processed successfully. Order is now {order.get_payment_status()}.'})
        except Exception as e:
            # Log the exception e (e.g., import logging; logger.error(str(e), exc_info=True))
            return JsonResponse({'status': 'error', 'message': f'An error occurred during refund processing: {str(e)}'}, status=500)

@method_decorator(ensure_csrf_cookie, name='dispatch') # Ensures CSRF cookie is set for AJAX, good practice
class ProcessCashPaymentModalView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order_number_str = request.POST.get('order_number')
        amount_str = request.POST.get('amount')

        if not order_number_str:
            return JsonResponse({'status': 'error', 'message': 'Order Number is required.'}, status=400)

        try:
            order = get_object_or_404(Order, order_number=order_number_str)
        except ValueError: # If order_id is not a valid integer
             return JsonResponse({'status': 'error', 'message': 'Invalid Order Number format.'}, status=400)

        amount_to_pay = order.balance_due() # Default to balance due

        if amount_str:
            try:
                posted_amount = Decimal(amount_str)
                if posted_amount > Decimal('0.00'):
                    # Cap payment at balance_due for this view's current logic
                    amount_to_pay = min(posted_amount, order.balance_due()) 
                    if amount_to_pay <= Decimal('0.00') and order.is_paid(): # Trying to pay 0 for already paid order
                         return JsonResponse({'status': 'info', 'message': 'Order is already fully paid.'}, status=200)
                else: # posted_amount is zero or negative
                    if order.balance_due() <= Decimal('0.00'): # Already paid or overpaid
                         return JsonResponse({'status': 'info', 'message': 'Order is already fully paid or overpaid.'}, status=200)
                    # else, amount_to_pay remains order.balance_due()
            except InvalidOperation:
                return JsonResponse({'status': 'error', 'message': 'Invalid amount format.'}, status=400)
        
        if amount_to_pay <= Decimal('0.00'): # This can happen if balance_due was 0 initially and no amount_str provided
            return JsonResponse({'status': 'info', 'message': 'No balance to pay for this order or order is already paid.'}, status=200)

        try:
            with transaction.atomic():
                payment = Payment.objects.create(
                    order=order,
                    amount=amount_to_pay, # Use calculated amount
                    payment_method=Payment.PAYMENT_METHOD_CASH,
                    payment_type=Payment.PAYMENT_TYPE_PAYMENT, # Specify payment type
                    status=Payment.STATUS_COMPLETED, # Cash is immediately completed
                    reference=uuid.uuid4() 
                )
                
                order.refresh_from_db() # Reload order to get the updated amount_paid and is_paid status
                if order.status == "Pending" and order.is_paid(): 
                    order.status = "Accepted" 
                    order.save(update_fields=['status'])
                
                PaymentTransaction.objects.create(
                    payment=payment,
                    transaction_id=f"cash_{payment.reference}",
                    status='success',
                    amount=payment.amount,
                    is_verified=True
                )

            success_message = f'Cash payment of ₵{amount_to_pay} recorded successfully. Order is now {order.get_payment_status()}.'
            return JsonResponse({'status': 'success', 'message': success_message})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class InitiatePaystackModalView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order_number_str = request.POST.get('order_number')
        mobile_number_raw = request.POST.get('mobile_number', '').strip()
        amount_str = request.POST.get('amount')

        if not order_number_str:
            return JsonResponse({'status': 'error', 'message': 'Order Number is required.'}, status=400)
        
        try:
            order = get_object_or_404(Order, order_number=order_number_str)
        except ValueError: # If order_id is not a valid integer
             return JsonResponse({'status': 'error', 'message': 'Invalid Order Number format.'}, status=400)

        amount_to_initiate = order.balance_due() # Default to balance due

        if amount_str:
            try:
                posted_amount = Decimal(amount_str)
                if posted_amount > Decimal('0.00'):
                    amount_to_initiate = min(posted_amount, order.balance_due())
                    if amount_to_initiate <= Decimal('0.00') and order.is_paid():
                         return JsonResponse({'status': 'info', 'message': 'Order is already fully paid.'}, status=200)
                else: # posted_amount is zero or negative
                    if order.balance_due() <= Decimal('0.00'):
                         return JsonResponse({'status': 'info', 'message': 'Order is already fully paid or overpaid.'}, status=200)
            except InvalidOperation:
                return JsonResponse({'status': 'error', 'message': 'Invalid amount format.'}, status=400)

        if amount_to_initiate <= Decimal('0.00'):
            return JsonResponse({'status': 'info', 'message': 'No balance to pay for this order or order is already paid.'}, status=200)

        # --- Start: Phone Number Validation Block ---
        cleaned_mobile_number_for_paystack = None
        if not mobile_number_raw:
            return JsonResponse({'status': 'error', 'message': 'Valid mobile number is required.'}, status=400)

        temp_number_for_validation = mobile_number_raw
        if temp_number_for_validation.startswith('0') and len(temp_number_for_validation) == 10 and temp_number_for_validation[1:].isdigit():
            cleaned_mobile_number_for_paystack = '233' + temp_number_for_validation[1:]
        elif temp_number_for_validation.startswith('+233') and len(temp_number_for_validation) == 13 and temp_number_for_validation[4:].isdigit():
            cleaned_mobile_number_for_paystack = temp_number_for_validation[1:]
        elif temp_number_for_validation.startswith('233') and len(temp_number_for_validation) == 12 and temp_number_for_validation[3:].isdigit():
            cleaned_mobile_number_for_paystack = temp_number_for_validation
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid mobile number format. Use 0XXXXXXXXX, +233XXXXXXXXX, or 233XXXXXXXXX.'}, status=400)
        
        if not (cleaned_mobile_number_for_paystack and cleaned_mobile_number_for_paystack.startswith('233') and len(cleaned_mobile_number_for_paystack) == 12 and cleaned_mobile_number_for_paystack[3:].isdigit()):
            return JsonResponse({'status': 'error', 'message': 'Processed mobile number is not in Paystack format (233XXXXXXXXX).'}, status=400)
        # --- End: Phone Number Validation Block ---

        try:
            with transaction.atomic():
                payment_reference = uuid.uuid4()
                # Check if a pending/processing payment already exists for this order with this method
                existing_payment = Payment.objects.filter(
                    order=order, 
                    payment_method=Payment.PAYMENT_METHOD_MOBILE,
                    status__in=[Payment.STATUS_PENDING, Payment.STATUS_PROCESSING]
                ).first()

                if existing_payment:
                    payment = existing_payment
                    payment.amount = amount_to_initiate # Update amount
                    payment.mobile_number = cleaned_mobile_number_for_paystack
                    # payment.reference = uuid.uuid4() # Consider if reference needs to change for retry
                    payment.paystack_reference = None 
                    payment.status = Payment.STATUS_PENDING
                    payment.payment_type = Payment.PAYMENT_TYPE_PAYMENT # Ensure type is payment
                    payment.save()
                else:
                    payment = Payment.objects.create(
                        order=order,
                        amount=amount_to_initiate, # Use determined amount
                        payment_method=Payment.PAYMENT_METHOD_MOBILE,
                        payment_type=Payment.PAYMENT_TYPE_PAYMENT, # Explicitly set type
                        status=Payment.STATUS_PENDING, 
                        reference=payment_reference,
                        mobile_number=cleaned_mobile_number_for_paystack
                    )

                paystack_secret = settings.PAYSTACK_SECRET_KEY
                paystack_url = "https://api.paystack.co/transaction/initialize"
                headers = {
                    "Authorization": f"Bearer {paystack_secret}",
                    "Content-Type": "application/json"
                }
                callback_url = request.build_absolute_uri(
                    reverse('payments:verify_payment', kwargs={'reference': str(payment.reference)})
                )
                payload_data = {
                    "email": f"customer_{order.customer_phone.replace('+', '').replace(' ', '') if order.customer_phone else str(order.id)}@example.com",
                    "amount": int(amount_to_initiate * 100), # Use amount_to_initiate
                    "currency": "GHS",
                    "reference": str(payment.reference),
                    "callback_url": callback_url,
                    "metadata": {
                        "order_id": order.id,
                        "payment_id": payment.id,
                        "customer_phone_submitted": mobile_number_raw,
                        "custom_fields": [{
                            "display_name": "Phone Number",
                            "variable_name": "phone_number",
                            "value": payment.mobile_number
                        }]
                    }
                }

                api_response = requests.post(paystack_url, headers=headers, json=payload_data, timeout=10)
                api_response_data = api_response.json()

                if api_response.status_code == 200 and api_response_data.get('status'):
                    authorization_url = api_response_data.get('data', {}).get('authorization_url')
                    paystack_api_reference = api_response_data.get('data', {}).get('reference', '')

                    if authorization_url:
                        payment.paystack_reference = paystack_api_reference 
                        payment.response_data = api_response_data
                        payment.status = Payment.STATUS_PROCESSING 
                        payment.save()

                        PaymentTransaction.objects.create(
                            payment=payment,
                            transaction_id=paystack_api_reference or str(uuid.uuid4()),
                            status='initialized',
                            amount=payment.amount,
                            response_data=api_response_data,
                            is_verified=False
                        )
                        return JsonResponse({
                            'status': 'success',
                            'authorization_url': authorization_url,
                            'reference': str(payment.reference) 
                        })
                    else:
                        payment.status = Payment.STATUS_FAILED
                        payment.response_data = api_response_data
                        payment.save()
                        return JsonResponse({'status': 'error', 'message': api_response_data.get('message', 'Paystack init failed: No authorization URL.')}, status=400)
                else:
                    payment.status = Payment.STATUS_FAILED
                    payment.response_data = api_response_data
                    payment.save()
                    return JsonResponse({'status': 'error', 'message': f"Paystack API error: {api_response_data.get('message', 'Unknown error')}"}, status=api_response.status_code or 400)

        except requests.exceptions.RequestException as e_req:
            if 'payment' in locals() and payment.pk:
                payment.status = Payment.STATUS_FAILED
                payment.notes = f"RequestException: {str(e_req)}"
                payment.save()
            return JsonResponse({'status': 'error', 'message': f'Network error during payment processing: {str(e_req)}'}, status=500)
        except Exception as e_gen:
            if 'payment' in locals() and payment.pk: 
                payment.status = Payment.STATUS_FAILED
                payment.notes = f"General Exception: {str(e_gen)}"
                payment.save()
            return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e_gen)}'}, status=500)

class TransactionDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying details of a payment transaction
    """
    model = Payment
    template_name = 'payments/transaction_detail.html'
    context_object_name = 'transaction'
    
    def dispatch(self, request, *args, **kwargs):
        """Only allow admin and frontdesk staff to access"""
        if not (request.user.is_admin() or request.user.is_frontdesk()):
            messages.error(request, "You don't have permission to view transaction details.")
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add related data to context"""
        context = super().get_context_data(**kwargs)
        
        # Get transaction history
        transaction_history = PaymentTransaction.objects.filter(
            payment=self.object
        ).order_by('-created_at')
        context['transaction_history'] = transaction_history
        
        # Get order items if order exists
        if self.object.order:
            order_items = self.object.order.items.all().select_related('menu_item')
            context['order_items'] = order_items
            
            # Calculate order total
            context['order_total'] = self.object.order.total_price
        
        # Add payment response data if available (for debugging)
        if self.object.response_data:
            # If it's stored as JSON string, parse it
            if isinstance(self.object.response_data, str):
                try:
                    context['response_data'] = json.loads(self.object.response_data)
                except json.JSONDecodeError:
                    context['response_data'] = self.object.response_data
            else:
                context['response_data'] = self.object.response_data
        
        return context

