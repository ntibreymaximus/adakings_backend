from rest_framework import serializers
from django.core.validators import MinValueValidator # Added import
from drf_spectacular.utils import extend_schema_field
from typing import Optional, Dict, List, Any
from .models import Payment, PaymentTransaction
from apps.orders.models import Order # For Order lookup
from decimal import Decimal

class PaymentTransactionSerializer(serializers.ModelSerializer):
    # Payment information
    payment_id = serializers.IntegerField(source='payment.id', read_only=True)
    payment_reference = serializers.UUIDField(source='payment.reference', read_only=True)
    payment_method = serializers.CharField(source='payment.payment_method', read_only=True)
    payment_method_display = serializers.CharField(source='payment.get_payment_method_display', read_only=True)
    payment_type = serializers.CharField(source='payment.payment_type', read_only=True)
    payment_type_display = serializers.CharField(source='payment.get_payment_type_display', read_only=True)
    payment_status = serializers.CharField(source='payment.status', read_only=True)
    payment_status_display = serializers.CharField(source='payment.get_status_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    # Order information
    order_id = serializers.IntegerField(source='payment.order.id', read_only=True)
    order_number = serializers.CharField(source='payment.order.order_number', read_only=True)
    order_status = serializers.CharField(source='payment.order.status', read_only=True)
    order_total_price = serializers.DecimalField(source='payment.order.total_price', max_digits=10, decimal_places=2, read_only=True)
    order_delivery_type = serializers.CharField(source='payment.order.delivery_type', read_only=True)
    
    # Customer information
    customer_phone = serializers.CharField(source='payment.order.customer_phone', read_only=True)
    
    # Delivery information
    delivery_location = serializers.CharField(source='payment.order.delivery_location.name', read_only=True)
    delivery_fee = serializers.DecimalField(source='payment.order.delivery_fee', max_digits=6, decimal_places=2, read_only=True)
    
    # Transaction status display
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            # Core transaction fields
            'id', 'transaction_id', 'status', 'status_display', 'amount', 'currency', 
            'response_data', 'is_verified', 'created_at', 'updated_at', 'time_ago',
            
            # Payment information
            'payment_id', 'payment_reference', 'payment_method', 'payment_method_display',
            'payment_type', 'payment_type_display', 'payment_status', 'payment_status_display',
            
            # Order information
            'order_id', 'order_number', 'order_status', 'order_total_price', 'order_delivery_type',
            
            # Customer information
            'customer_phone',
            
            # Delivery information
            'delivery_location', 'delivery_fee'
        ]
        read_only_fields = ('created_at', 'updated_at')
    
    @extend_schema_field(serializers.CharField(help_text="Time since the transaction was last updated"))
    def get_time_ago(self, obj) -> str:
        """Get the time since the transaction was last updated"""
        return obj.time_ago()

class PaymentSerializer(serializers.ModelSerializer):
    transactions = PaymentTransactionSerializer(many=True, read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    # Order information
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)
    order_total_price = serializers.DecimalField(source='order.total_price', max_digits=10, decimal_places=2, read_only=True)
    order_delivery_type = serializers.CharField(source='order.delivery_type', read_only=True)
    order_notes = serializers.CharField(source='order.notes', read_only=True)
    
    # Customer information
    customer_phone = serializers.CharField(source='order.customer_phone', read_only=True)
    
    # Delivery information
    delivery_location = serializers.CharField(source='order.delivery_location.name', read_only=True)
    delivery_fee = serializers.DecimalField(source='order.delivery_fee', max_digits=6, decimal_places=2, read_only=True)
    
    # Payment status display
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Order payment calculations
    order_amount_paid = serializers.SerializerMethodField()
    order_balance_due = serializers.SerializerMethodField()
    order_payment_status = serializers.SerializerMethodField()
    
    # For write operations, we might want to accept order_id or order_number
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), write_only=True)
    
    class Meta:
        model = Payment
        fields = [
            # Payment core fields
            'id', 'order', 'order_id', 'order_number', 'amount', 'payment_method', 
            'payment_method_display', 'status', 'status_display', 'payment_type', 
            'payment_type_display', 'reference', 'mobile_number', 'paystack_reference',
            'wix_order_number', 'response_data', 'notes', 'created_at', 'updated_at', 'time_ago',
            
            # Order information
            'order_status', 'order_total_price', 'order_delivery_type', 'order_notes',
            'order_amount_paid', 'order_balance_due', 'order_payment_status',
            
            # Customer information
            'customer_phone',
            
            # Delivery information
            'delivery_location', 'delivery_fee',
            
            # Related transactions
            'transactions'
        ]
        read_only_fields = ('reference', 'paystack_reference', 'response_data', 'created_at', 'updated_at')
    
    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Total amount paid for the order"))
    def get_order_amount_paid(self, obj) -> Decimal:
        """Get the total amount paid for the order"""
        return obj.order.amount_paid()
    
    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Balance due for the order"))
    def get_order_balance_due(self, obj) -> Decimal:
        """Get the balance due for the order"""
        return obj.order.balance_due()
    
    @extend_schema_field(serializers.CharField(help_text="Payment status of the order"))
    def get_order_payment_status(self, obj) -> str:
        """Get the payment status of the order"""
        return obj.order.get_payment_status()
    
    @extend_schema_field(serializers.CharField(help_text="Time since the payment was last updated"))
    def get_time_ago(self, obj) -> str:
        """Get the time since the payment was last updated"""
        return obj.time_ago()

    def validate(self, data):
        order = data.get('order')
        amount = data.get('amount')
        payment_type = data.get('payment_type', self.instance.payment_type if self.instance else Payment.PAYMENT_TYPE_PAYMENT)
        payment_method = data.get('payment_method')

        if not order and not self.instance: # Required on create
            raise serializers.ValidationError({"order": "Order is required for a payment."})
        
        active_order = order or (self.instance.order if self.instance else None)
        if not active_order:
             raise serializers.ValidationError("Order context is missing for validation.")

        if payment_type == Payment.PAYMENT_TYPE_PAYMENT:
            # For new payments, amount should not make the order excessively overpaid.
            # This is a basic check. More sophisticated checks might involve order.balance_due().
            pass # Model's clean method has some checks, view logic will be more precise.
        elif payment_type == Payment.PAYMENT_TYPE_REFUND:
            if amount <= Decimal('0.00'):
                raise serializers.ValidationError({"amount": "Refund amount must be positive."})
            # Check if refund amount exceeds what has been paid
            if active_order.amount_paid() < amount:
                raise serializers.ValidationError({"amount": f"Refund amount (₵{amount}) cannot exceed the net amount paid (₵{active_order.amount_paid()})."})

        if payment_method == Payment.PAYMENT_METHOD_PAYSTACK_API and not data.get('mobile_number'):
            # This validation might be conditional if mobile_number can be taken from order or user profile later
            if not (self.instance and self.instance.mobile_number and 'mobile_number' not in data): # Allow update without re-specifying if already set
                raise serializers.ValidationError({"mobile_number": "Mobile number is required for mobile payments."})
        return data

class PaymentInitiateSerializer(serializers.Serializer):
    order_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_METHOD_CHOICES)
    mobile_number = serializers.CharField(max_length=15, required=False, allow_blank=True) # Required if payment_method is PAYSTACK(API)
    wix_order_number = serializers.CharField(max_length=100, required=False, allow_blank=True) # Required if payment_method is PAID_ON_WIX
    payment_type = serializers.ChoiceField(choices=Payment.PAYMENT_TYPE_CHOICES, default=Payment.PAYMENT_TYPE_PAYMENT)

    def validate_order_number(self, value):
        try:
            order = Order.objects.get(order_number=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order with this order number does not exist.")
        # Store order on serializer for access in other validation methods or view
        self.context['order'] = order 
        return value

    def validate_mobile_number(self, value):
        payment_method = self.initial_data.get('payment_method')
        if payment_method == Payment.PAYMENT_METHOD_PAYSTACK_API and not value:
            raise serializers.ValidationError("Mobile number is required for Paystack API payments.")
        # Add more specific Ghanaian phone number validation if necessary
        return value
    
    def validate_wix_order_number(self, value):
        payment_method = self.initial_data.get('payment_method')
        if payment_method == Payment.PAYMENT_METHOD_WIX and not value:
            raise serializers.ValidationError("Wix order number is required for Paid on Wix payments.")
        return value

    def validate(self, data):
        order = self.context.get('order') # Retrieve order from context
        amount = data.get('amount')
        payment_type = data.get('payment_type')

        if not order: # Should be caught by validate_order_number, but as a safeguard
            raise serializers.ValidationError("Order validation failed.")

        if payment_type == Payment.PAYMENT_TYPE_PAYMENT:
            if amount > order.balance_due():
                # Allow overpayment, but maybe log or warn. For now, we cap at balance_due for simplicity in initiation.
                # Or, let it through and the order.get_payment_status() will show OVERPAID.
                # For this serializer, let's be strict: you pay up to balance_due.
                # If client wants to overpay, they should know the balance and set amount accordingly, or a different endpoint should handle it.
                # For now, we allow paying more than balance_due. The order model will reflect this.
                pass 
        elif payment_type == Payment.PAYMENT_TYPE_REFUND:
            if amount > order.amount_paid():
                raise serializers.ValidationError(f"Refund amount cannot exceed the total amount paid for the order (₵{order.amount_paid()}).")
        return data

class PaystackWebhookSerializer(serializers.Serializer):
    event = serializers.CharField()
    data = serializers.JSONField() # Can be further nested if structure is known and fixed

