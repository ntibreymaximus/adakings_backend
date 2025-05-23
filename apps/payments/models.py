from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.orders.models import Order
from decimal import Decimal
from uuid import uuid4


class Payment(models.Model):
    """Model for tracking payments for orders"""
    # Payment Methods
    PAYMENT_METHOD_CASH = 'cash'
    PAYMENT_METHOD_MOBILE = 'mobile_money'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_CASH, 'Cash'),
        (PAYMENT_METHOD_MOBILE, 'Mobile Money'),
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
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or comments about this payment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        # Validate amount does not exceed order total
        if self.amount > self.order.total_price:
            raise ValidationError("Payment amount cannot exceed order total")
        
        # Mobile payment specific validations - only in second step
        if self.payment_method == self.PAYMENT_METHOD_MOBILE:
            # Skip validation in first step (when creating initial payment)
            if getattr(self, '_skip_mobile_validation', False):
                pass
            # In second step, validate mobile number
            elif not self.mobile_number:
                raise ValidationError("Mobile number is required for mobile payments")
        else:
            # For cash payments, mobile number and paystack_reference should be empty
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
    
    def get_absolute_url(self):
        return reverse('payments:payment_detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id} ({self.get_payment_method_display()}) - {self.get_status_display()}"
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']


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
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.get_status_display()} ({self.payment.reference})"
    
    class Meta:
        verbose_name = _('Payment Transaction')
        verbose_name_plural = _('Payment Transactions')
        ordering = ['-created_at']
        
    def mark_as_verified(self):
        """Mark transaction as verified"""
        self.is_verified = True
        self.save(update_fields=['is_verified'])
