from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.orders.models import Order
from decimal import Decimal
from uuid import uuid4
from django.utils.timesince import timesince


class Payment(models.Model):
    """Model for tracking payments for orders"""
    PAYMENT_TYPE_PAYMENT = 'payment'
    PAYMENT_TYPE_REFUND = 'refund'
    PAYMENT_TYPE_CHOICES = [
        (PAYMENT_TYPE_PAYMENT, 'Payment'),
        (PAYMENT_TYPE_REFUND, 'Refund'),
    ]

    # Payment Methods
    PAYMENT_METHOD_CASH = 'CASH'
    PAYMENT_METHOD_TELECEL_CASH = 'TELECEL CASH'
    PAYMENT_METHOD_MTN_MOMO = 'MTN MOMO'
    PAYMENT_METHOD_PAYSTACK_USSD = 'PAYSTACK(USSD)'
    PAYMENT_METHOD_PAYSTACK_API = 'PAYSTACK(API)'
    PAYMENT_METHOD_WIX = 'PAID_ON_WIX'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_CASH, 'Cash'),
        (PAYMENT_METHOD_TELECEL_CASH, 'Telecel Cash'),
        (PAYMENT_METHOD_MTN_MOMO, 'MTN MoMo'),
        (PAYMENT_METHOD_PAYSTACK_USSD, 'Paystack (USSD)'),
        (PAYMENT_METHOD_PAYSTACK_API, 'Paystack (API)'),
        (PAYMENT_METHOD_WIX, 'Paid on Wix'),
    ]
    
    # Payment Statuses
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    PAYMENT_STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    # Fields
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_CASH
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=STATUS_PENDING
    )
    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_TYPE_CHOICES,
        default=PAYMENT_TYPE_PAYMENT,
        help_text="Type of transaction (Payment or Refund)"
    )
    reference = models.UUIDField(
        default=uuid4,
        unique=True,
        editable=False
    )
    mobile_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Mobile number used for mobile payment in format +233XXXXXXXXX or 0XXXXXXXXX"
    )
    paystack_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reference from Paystack if mobile payment"
    )
    response_data = models.JSONField(
        blank=True,
        null=True,
        help_text="Payment processor response data"
    )
    wix_order_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Wix order number for payments made on Wix platform"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or comments about this payment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        super().clean() # Call superclass's clean method

        if not self.order_id: # Check if order is linked before accessing self.order
            # This can happen if the Payment instance is not yet associated with an Order
            # For example, during form validation before the order foreign key is set.
            # In such cases, order-dependent validations should be skipped or handled carefully.
            return

        # Validate amount based on payment_type
        if self.payment_type == self.PAYMENT_TYPE_PAYMENT:
            # For a new payment, it shouldn't typically make the order excessively overpaid.
            # More precise logic for total paid vs. total_price will be in the view/form.
            # A very basic check: a single payment shouldn't be drastically larger than the order total.
            if self.amount > (self.order.total_price * Decimal('1.5')): # e.g., allow up to 50% overpayment for a single transaction
                # raise ValidationError(f"Payment amount (₵{self.amount}) seems too large for the order total (₵{self.order.total_price}).")
                pass # Decided to handle this with more nuance in views

        elif self.payment_type == self.PAYMENT_TYPE_REFUND:
            # Ensure refund amount is positive
            if self.amount <= Decimal('0.00'):
                raise ValidationError("Refund amount must be positive.")
            # More complex validation (e.g., not refunding more than available) will be in the view/form
            # as it requires knowing the order's current payment state.

        # Mobile payment specific validations (existing logic)
        if self.payment_method == self.PAYMENT_METHOD_PAYSTACK_API:
            if not getattr(self, '_skip_mobile_validation', False) and not self.mobile_number:
                raise ValidationError({"mobile_number": "Mobile number is required for Paystack API payments."})
        elif self.payment_type == self.PAYMENT_TYPE_PAYMENT: # For non-Paystack-API 'payment' types
             # Ensure mobile number and Paystack ref are clear if not Paystack API
            if self.payment_method != self.PAYMENT_METHOD_PAYSTACK_API:
                self.mobile_number = None
                self.paystack_reference = None
    
    def generate_reference(self):
        # Generate unique payment reference
        self.reference = uuid4()
    
    def initiate_payment(self):
        # Placeholder for initiating mobile payments via Paystack
        pass
    
    def verify_payment(self):
        # Placeholder for verifying Paystack payments
        pass
    
    def mark_as_completed(self):
        self.status = self.STATUS_COMPLETED
        self.save(update_fields=['status'])
    
    def mark_as_failed(self):
        self.status = self.STATUS_FAILED
        self.save(update_fields=['status'])
    
    def is_completed(self):
        return self.status == self.STATUS_COMPLETED
    
    def time_ago(self):
        """Return the time since the payment was last updated in a human-readable format."""
        from django.utils import timezone
        
        now = timezone.now()
        time_diff = now - self.updated_at
        
        # If updated less than 30 seconds ago, show "Just now"
        if time_diff.total_seconds() < 30:
            return "Just now"
        
        # Use Django's timesince for everything else
        return timesince(self.updated_at, now) + " ago"
    
    def get_absolute_url(self):
        return reverse('payments:payment_detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        type_str = f" ({self.get_payment_type_display()})" if self.payment_type == self.PAYMENT_TYPE_REFUND else ""
        order_identifier = self.order.order_number if self.order else "N/A"
        return f"Payment {self.id} for Order {order_identifier}{type_str} ({self.get_payment_method_display()}) - {self.get_status_display()} - ₵{self.amount}"
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-updated_at']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['payment_type']),
            models.Index(fields=['reference']),
            models.Index(fields=['paystack_reference']),
            models.Index(fields=['order', 'status']),  # Composite index
        ]


class PaymentTransaction(models.Model):
    """Model for tracking payment transactions and Paystack responses"""
    TRANSACTION_STATUS_CHOICES = [
        ('initialized', 'Initialized'),
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
    ]
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True
    )
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='initialized'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(
        max_length=3,
        default='GHS',
        help_text="Currency code (GHS for Ghana Cedis)"
    )
    response_data = models.JSONField(
        blank=True,
        null=True,
        help_text="Transaction response data from payment processor"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this transaction has been verified"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def time_ago(self):
        """Return the time since the transaction was last updated in a human-readable format."""
        from django.utils import timezone
        
        now = timezone.now()
        time_diff = now - self.updated_at
        
        # If updated less than 30 seconds ago, show "Just now"
        if time_diff.total_seconds() < 30:
            return "Just now"
        
        # Use Django's timesince for everything else
        return timesince(self.updated_at, now) + " ago"
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.get_status_display()} ({self.payment.reference})"
    
    class Meta:
        verbose_name = _('Payment Transaction')
        verbose_name_plural = _('Payment Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['payment']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['is_verified']),
        ]
        
    def mark_as_verified(self):
        """Mark transaction as verified"""
        self.is_verified = True
        self.save(update_fields=['is_verified'])
