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
from .models import Payment, PaymentTransaction
from apps.orders.models import Order
from .forms import PaymentForm, PaystackPaymentForm
import requests
import json
import uuid
import hmac
import hashlib


class PaymentMethodSelectionView(LoginRequiredMixin, FormView):
    """View for selecting payment method"""
    template_name = 'payments/process_payment.html'
    form_class = PaymentForm
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.order = get_object_or_404(Order, id=kwargs.get('order_id'))
        print(f"[PaymentMethodSelectionView] Setup with order #{self.order.id}, total: ${self.order.total_price}")
    
    def get_form_kwargs(self):
        """Pass the order to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.order
        kwargs['step'] = 'select_method'  # First step - selecting payment method
        print(f"[PaymentMethodSelectionView] Form kwargs prepared with order #{self.order.id}")
        return kwargs
        
    def get_initial(self):
        """Set initial form values."""
        initial = {
            'amount': self.order.total_price,
            'payment_method': Payment.PAYMENT_METHOD_CASH,  # Default to cash
        }
        print(f"[PaymentMethodSelectionView] Initial form data: {initial}")
        return initial
    
    def get_context_data(self, **kwargs):
        """Add order to the template context."""
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        
        # Add form errors to context for debugging
        form = context.get('form')
        if form and not form.is_valid() and self.request.method == 'POST':
            context['form_errors'] = form.errors
            print(f"[PaymentMethodSelectionView] Form errors: {form.errors}")
            
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
            print(f"[PaymentMethodSelectionView] No payment object, redirecting to order detail")
            return reverse('orders:order_detail', kwargs={'pk': self.order.id})
            
        print(f"[PaymentMethodSelectionView] Payment #{payment.id} method: {payment.payment_method}")
        if payment.payment_method == Payment.PAYMENT_METHOD_CASH:
            url = reverse('payments:cash_payment', kwargs={'payment_id': payment.id})
            print(f"[PaymentMethodSelectionView] Redirecting to cash payment: {url}")
            return url
        elif payment.payment_method == Payment.PAYMENT_METHOD_MOBILE:
            url = reverse('payments:mobile_payment', kwargs={'payment_id': payment.id})
            print(f"[PaymentMethodSelectionView] Redirecting to mobile payment: {url}")
            return url
            
        url = reverse('orders:order_detail', kwargs={'pk': self.order.id})
        print(f"[PaymentMethodSelectionView] Redirecting to order detail: {url}")
        return url
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        print(f"[PaymentMethodSelectionView] Form invalid: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Error in {field}: {error}")
        
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """Process the valid form."""
        try:
            print(f"[PaymentMethodSelectionView] Form valid, cleaned data: {form.cleaned_data}")
            
            # Save the form to create the payment
            self.payment = form.save(commit=False)
            
            # Set additional fields
            self.payment.reference = str(uuid.uuid4())
            self.payment.save()
            
            print(f"[PaymentMethodSelectionView] Payment created: #{self.payment.id}, method: {self.payment.payment_method}")
            
            # Redirect to appropriate payment view based on payment method
            success_url = self.get_success_url()
            print(f"[PaymentMethodSelectionView] Redirecting to: {success_url}")
            return redirect(success_url)
            
        except Exception as e:
            print(f"[PaymentMethodSelectionView] Error processing payment: {str(e)}")
            messages.error(self.request, f"Error processing payment: {str(e)}")
            return self.form_invalid(form)


class CashPaymentView(LoginRequiredMixin, DetailView):
    """View for processing cash payments"""
    model = Payment
    template_name = 'payments/cash_payment.html'
    context_object_name = 'payment'
    pk_url_kwarg = 'payment_id'
    
    def get_queryset(self):
        return super().get_queryset().filter(payment_method=Payment.PAYMENT_METHOD_CASH)
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        payment = self.get_object()
        order = payment.order
        
        # Process cash payment
        payment.status = Payment.STATUS_COMPLETED
        payment.save()
        
        # Update order status
        if order.status == 'Pending':
            order.status = 'Confirmed'
            order.save()
        
        messages.success(request, 'Cash payment recorded successfully!')
        return redirect('orders:order_detail', pk=order.id)


class MobilePaymentView(LoginRequiredMixin, FormView):
    """View for initiating mobile payments via Paystack"""
    template_name = 'payments/mobile_payment.html'
    form_class = PaystackPaymentForm
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.payment = get_object_or_404(
            Payment, 
            id=kwargs.get('payment_id'),
            payment_method=Payment.PAYMENT_METHOD_MOBILE
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment'] = self.payment
        context['order'] = self.payment.order
        return context
    
    def form_valid(self, form):
        payment = self.payment
        order = payment.order
        mobile_number = form.cleaned_data['phone_number']
        
        # Save mobile number to payment
        payment.mobile_number = mobile_number
        payment.status = Payment.STATUS_PROCESSING
        payment.save()
        
        # Prepare Paystack API call
        paystack_secret = settings.PAYSTACK_SECRET_KEY
        url = "https://api.paystack.co/transaction/initialize"
        
        headers = {
            "Authorization": f"Bearer {paystack_secret}",
            "Content-Type": "application/json"
        }
        
        callback_url = self.request.build_absolute_uri(
            reverse('payments:verify_payment', kwargs={'reference': payment.reference})
        )
        
        data = {
            "email": f"customer_{order.customer_phone.replace('+', '').replace(' ', '')}@example.com",  # Generate email from customer phone
            "amount": int(payment.amount * 100),  # Convert to pesewas (or lowest currency unit)
            "currency": "GHS",
            "reference": str(payment.reference),
            "callback_url": callback_url,
            "metadata": {
                "order_id": order.id,
                "payment_id": payment.id,
                "custom_fields": [
                    {
                        "display_name": "Phone Number",
                        "variable_name": "phone_number",
                        "value": mobile_number
                    }
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status'):
                # Create transaction record
                transaction = PaymentTransaction.objects.create(
                    payment=payment,
                    transaction_id=response_data.get('data', {}).get('reference', ''),
                    status='initialized',
                    amount=payment.amount,
                    response_data=response_data
                )
                
                # Update payment with Paystack reference
                payment.paystack_reference = response_data.get('data', {}).get('reference', '')
                payment.response_data = response_data
                payment.save()
                
                # Redirect to Paystack payment URL
                authorization_url = response_data.get('data', {}).get('authorization_url')
                if authorization_url:
                    return redirect(authorization_url)
                else:
                    messages.error(self.request, "Payment initialization failed. Please try again.")
            else:
                messages.error(self.request, f"Payment failed: {response_data.get('message', 'Unknown error')}")
                payment.status = Payment.STATUS_FAILED
                payment.save()
        except Exception as e:
            messages.error(self.request, f"Payment processing error: {str(e)}")
            payment.status = Payment.STATUS_FAILED
            payment.save()
        
        return redirect('payments:payment_failed')


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
            
            # Update order status
            order = payment.order
            if order.status == 'Pending':
                order.status = 'Confirmed'
                order.save()
            
            # Update transaction status
            transaction = payment.transactions.first()
            if transaction:
                transaction.is_verified = True
                transaction.status = 'success'
                transaction.save()
            
            messages.success(request, 'Payment verified successfully!')
            return redirect('payments:payment_success')
        else:
            payment.status = Payment.STATUS_FAILED
            payment.save()
            
            # Update transaction status
            transaction = payment.transactions.first()
            if transaction:
                transaction.status = 'failed'
                transaction.save()
            
            messages.error(request, 'Payment verification failed.')
            return redirect('payments:payment_failed')
    
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
        print(f"[TransactionListView] Filtering transactions")
        queryset = Payment.objects.all().select_related('order').order_by('-created_at')
        
        # Filter by payment method
        payment_method = self.request.GET.get('payment_method')
        if payment_method:
            print(f"[TransactionListView] Filtering by payment method: {payment_method}")
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            print(f"[TransactionListView] Filtering by status: {status}")
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                print(f"[TransactionListView] Filtering by start date: {start_date}")
                queryset = queryset.filter(created_at__date__gte=start_date)
            except ValueError:
                print(f"[TransactionListView] Invalid start date format: {start_date}")
                pass
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                # Add one day to include the end date in the range
                end_date = end_date + timedelta(days=1)
                print(f"[TransactionListView] Filtering by end date: {end_date}")
                queryset = queryset.filter(created_at__date__lt=end_date)
            except ValueError:
                print(f"[TransactionListView] Invalid end date format: {end_date}")
                pass
        
        # Search by customer name or order ID
        search_query = self.request.GET.get('q')
        if search_query:
            print(f"[TransactionListView] Searching for: {search_query}")
            queryset = queryset.filter(
                Q(order__customer_name__icontains=search_query) |
                Q(order__id__icontains=search_query) |
                Q(reference__icontains=search_query)
            )
        
        print(f"[TransactionListView] Found {queryset.count()} transactions")
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter choices and statistics to context"""
        context = super().get_context_data(**kwargs)
        print(f"[TransactionListView] Preparing context data")
        
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
        
        print(f"[TransactionListView] Context prepared: {context['transaction_counts']}")
        return context


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
        print(f"[TransactionDetailView] Preparing context for transaction #{self.object.id}")
        
        # Get transaction history
        transaction_history = PaymentTransaction.objects.filter(
            payment=self.object
        ).order_by('-created_at')
        context['transaction_history'] = transaction_history
        print(f"[TransactionDetailView] Found {transaction_history.count()} transaction history entries")
        
        # Get order items if order exists
        if self.object.order:
            order_items = self.object.order.items.all().select_related('menu_item')
            context['order_items'] = order_items
            print(f"[TransactionDetailView] Found {order_items.count()} order items")
            
            # Calculate order total
            context['order_total'] = self.object.order.total_price
        
        # Add payment response data if available (for debugging)
        if self.object.response_data:
            # If it's stored as JSON string, parse it
            if isinstance(self.object.response_data, str):
                try:
                    context['response_data'] = json.loads(self.object.response_data)
                    print(f"[TransactionDetailView] Parsed JSON response data")
                except json.JSONDecodeError:
                    context['response_data'] = self.object.response_data
                    print(f"[TransactionDetailView] Could not parse response data as JSON")
            else:
                context['response_data'] = self.object.response_data
                print(f"[TransactionDetailView] Added response data to context")
        
        return context

