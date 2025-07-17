
# In adakings_backend/apps/orders/serializers.py

# Ensure these imports are present
from decimal import Decimal
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from typing import Optional, Dict, List, Any
from apps.menu.models import MenuItem
from .models import Order, OrderItem # OrderItem model no longer has parent_item
from apps.deliveries.models import DeliveryLocation
import logging

logger = logging.getLogger(__name__)

@extend_schema_field(serializers.CharField(help_text="Delivery location name or ID"))
class DeliveryLocationField(serializers.Field):
    """Custom field that accepts either DeliveryLocation ID or name"""
    
    def to_representation(self, value) -> Optional[str]:
        """Convert DeliveryLocation instance to its name for serialization"""
        if value is None:
            return None
        return value.name
    
    def to_internal_value(self, data) -> Optional[DeliveryLocation]:
        """Convert input data (ID or name) to DeliveryLocation instance"""
        if data is None:
            return None
        
        # If it's an integer, treat as ID
        if isinstance(data, int) or (isinstance(data, str) and data.isdigit()):
            try:
                return DeliveryLocation.objects.get(id=int(data), is_active=True)
            except DeliveryLocation.DoesNotExist:
                raise serializers.ValidationError(f"Delivery location with ID {data} not found or not active.")
        
        # If it's a string, treat as name
        if isinstance(data, str):
            try:
                return DeliveryLocation.objects.get(name=data, is_active=True)
            except DeliveryLocation.DoesNotExist:
                raise serializers.ValidationError(f"Delivery location '{data}' not found or not active.")
        
        raise serializers.ValidationError("Invalid delivery location data. Expected ID or name.")

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(), 
        source='menu_item',
    )
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    item_type = serializers.CharField(source='menu_item.item_type', read_only=True)

    class Meta:
        model = OrderItem
        fields = [ # parent_item removed from this list
            'id', 'menu_item_id', 'menu_item_name', 'item_type', 
            'quantity', 'unit_price', 'subtotal', 'notes'
        ]
        read_only_fields = ['subtotal', 'item_type']
        extra_kwargs = {
            'unit_price': {'required': False, 'allow_null': True},
            # parent_item extra_kwargs removed
        }

    def validate_menu_item_id(self, menu_item_instance):
        if not menu_item_instance.is_available:
            raise serializers.ValidationError(f"Menu item '{menu_item_instance.name}' is not currently available.")
        return menu_item_instance

    def validate(self, data):
        menu_item = data.get('menu_item')
        
        unit_price = data.get('unit_price', self.instance.unit_price if self.instance else None)

        if menu_item and (unit_price is None or unit_price == Decimal('0.00')):
            data['unit_price'] = menu_item.price
        elif unit_price is None: 
            is_create_operation = not self.instance
            if is_create_operation and not menu_item:
                 raise serializers.ValidationError({"menu_item_id": ["Menu item is required to determine price for new items."]})
            if menu_item and data.get('unit_price') is None :
                if menu_item.price is not None and menu_item.price > Decimal('0.00'):
                    data['unit_price'] = menu_item.price
                else:
                    raise serializers.ValidationError({"unit_price": [f"Price for menu item '{menu_item.name}' is not valid or not set."]})
        
        quantity = data.get('quantity', self.instance.quantity if self.instance else None)
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": ["Quantity must be a positive integer."]})
            
        return data

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    amount_overpaid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_status = serializers.SerializerMethodField()
    payment_mode = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    delivery_location = DeliveryLocationField(allow_null=True, required=False)
    # Use the historical fields directly, not from the relationship
    delivery_location_name = serializers.CharField(read_only=True)
    delivery_location_fee = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    effective_delivery_location_name = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    assigned_rider_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_phone',
            'delivery_type', 'delivery_location', 'delivery_location_name', 'delivery_location_fee',
            'custom_delivery_location', 'custom_delivery_fee', 'effective_delivery_location_name',
            'status', 'total_price', 'delivery_fee', 'notes', 'created_at', 'updated_at',
            'items', 'amount_paid', 'balance_due', 'amount_overpaid', 'refund_amount',
            'payment_status', 'payment_mode', 'payments', 'time_ago', 'assigned_rider_name'
        ]
        read_only_fields = ['order_number', 'total_price', 'created_at', 'updated_at', 'delivery_location_name', 'delivery_location_fee']
        extra_kwargs = {
            'customer_phone': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    
    @extend_schema_field(serializers.CharField(help_text="Effective delivery location name"))
    def get_effective_delivery_location_name(self, obj) -> str:
        """Get the effective delivery location name (from DeliveryLocation or custom)"""
        return obj.get_effective_delivery_location_name()
    
    def validate(self, data):
        """
        Validate that customer phone and location are provided when delivery is selected.
        """
        delivery_type = data.get('delivery_type', self.instance.delivery_type if self.instance else 'Pickup')
        customer_phone = data.get('customer_phone', self.instance.customer_phone if self.instance else None)
        delivery_location = data.get('delivery_location', self.instance.delivery_location if self.instance else None)
        custom_delivery_location = data.get('custom_delivery_location', self.instance.custom_delivery_location if self.instance else None)
        custom_delivery_fee = data.get('custom_delivery_fee', self.instance.custom_delivery_fee if self.instance else None)
        
        if delivery_type == 'Delivery':
            errors = {}
            
            # Check if this is a special delivery type that doesn't require phone
            special_delivery_names = ["Bolt Delivery"]
            is_special_delivery = (
                delivery_location and 
                hasattr(delivery_location, 'name') and 
                delivery_location.name in special_delivery_names
            )
            
            # Check customer phone (except for Bolt and WIX deliveries)
            if not is_special_delivery and (not customer_phone or customer_phone.strip() == ''):
                errors['customer_phone'] = ['Customer phone number is required for delivery orders.']
            
            # Check that either delivery_location OR custom_delivery_location is provided
            if not delivery_location and not custom_delivery_location:
                errors['delivery_location'] = ['Either a delivery location or custom location name is required for delivery orders.']
            
            # If custom location is provided, custom fee must also be provided
            if custom_delivery_location and custom_delivery_fee is None:
                errors['custom_delivery_fee'] = ['Custom delivery fee is required when using a custom delivery location.']
            
            # Cannot specify both delivery_location and custom fields
            if delivery_location and custom_delivery_location:
                errors['custom_delivery_location'] = ['Cannot specify both a delivery location and custom location. Choose one.']
            
            if errors:
                raise serializers.ValidationError(errors)
        
        return data
    
    @extend_schema_field(serializers.CharField(help_text="Payment status of the order"))
    def get_payment_status(self, obj) -> str:
        """Get the payment status based on related payments"""
        return obj.get_payment_status()
    
    @extend_schema_field(serializers.CharField(help_text="Most recent payment method used", allow_null=True))
    def get_payment_mode(self, obj) -> Optional[str]:
        """Get the most recent payment method used"""
        latest_payment = obj.payments.filter(
            status='completed',
            payment_type='payment'
        ).order_by('-created_at').first()
        
        if latest_payment:
            return latest_payment.payment_method
        return None
    
    @extend_schema_field(serializers.ListField(child=serializers.DictField(), help_text="List of payments for this order"))
    def get_payments(self, obj) -> List[Dict[str, Any]]:
        """Get all payments for this order with basic details"""
        payments = obj.payments.all().order_by('-created_at')
        return [
            {
                'id': payment.id,
                'reference': str(payment.reference),
                'amount': payment.amount,
                'payment_method': payment.payment_method,
                'payment_type': payment.payment_type,
                'status': payment.status,
                'mobile_number': payment.mobile_number,
                'notes': payment.notes,
                'created_at': payment.created_at,
                'updated_at': payment.updated_at,
                'time_ago': payment.time_ago()
            }
            for payment in payments
        ]
    
    @extend_schema_field(serializers.CharField(help_text="Time since the order was last updated"))
    def get_time_ago(self, obj) -> str:
        """Get the time since the order was last updated"""
        return obj.time_ago()
    
    @extend_schema_field(serializers.CharField(help_text="Name of the assigned delivery rider", allow_null=True))
    def get_assigned_rider_name(self, obj) -> Optional[str]:
        """Get the name of the assigned delivery rider if any"""
        # Check if this is a Bolt order
        if obj.delivery_location:
            if obj.delivery_location.name == "Bolt Delivery":
                return "Bolt-Delivery"
        
        # For regular orders, check delivery assignment
        try:
            if hasattr(obj, 'delivery_assignment') and obj.delivery_assignment:
                return obj.delivery_assignment.rider.name
        except AttributeError:
            pass
        return None

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        order.calculate_total() # Recalculate total after items are added
        order.save() # Save again to store the new total
        return order

    def update(self, instance, validated_data):
        # Prevent editing of fulfilled and paid orders
        if instance.status == 'Fulfilled' and instance.is_paid():
            raise serializers.ValidationError(
                "Cannot edit orders that are both fulfilled and fully paid."
            )
        
        items_data = validated_data.pop('items', None)

        # Update Order instance fields
        instance.customer_phone = validated_data.get('customer_phone', instance.customer_phone)
        instance.delivery_type = validated_data.get('delivery_type', instance.delivery_type)
        
        # Handle delivery location properly - use 'delivery_location' key if present, otherwise keep current
        if 'delivery_location' in validated_data:
            instance.delivery_location = validated_data['delivery_location']
            # Clear custom fields when using delivery location
            if instance.delivery_location:
                instance.custom_delivery_location = None
                instance.custom_delivery_fee = None
        if 'custom_delivery_location' in validated_data:
            instance.custom_delivery_location = validated_data['custom_delivery_location']
            # Clear delivery location when using custom location
            if instance.custom_delivery_location:
                instance.delivery_location = None
        if 'custom_delivery_fee' in validated_data:
            instance.custom_delivery_fee = validated_data['custom_delivery_fee']
            
        # Clear delivery location fields when switching to pickup
        if instance.delivery_type == 'Pickup':
            instance.delivery_location = None
            instance.custom_delivery_location = None
            instance.custom_delivery_fee = None
            
        instance.status = validated_data.get('status', instance.status)
        instance.notes = validated_data.get('notes', instance.notes)
        # delivery_fee and total_price are recalculated, not directly set from validated_data

        if items_data is not None:
            # Clear existing items and add new ones
            # This is a simple approach. For more complex scenarios, you might want to update existing items
            # or handle partial updates of items.
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        
        # Recalculate delivery fee based on potentially new delivery type/location
        old_delivery_fee = instance.delivery_fee
        instance.delivery_fee = instance._calculate_delivery_fee()
        logger.debug(f"Delivery fee changed from {old_delivery_fee} to {instance.delivery_fee} for order: {instance.id}")
        
        # Force a refresh from database to ensure we have all the latest items
        if items_data is not None:
            # Store current field values before refresh
            delivery_type = instance.delivery_type
            delivery_location = instance.delivery_location
            custom_delivery_location = instance.custom_delivery_location
            custom_delivery_fee = instance.custom_delivery_fee
            customer_phone = instance.customer_phone
            status = instance.status
            notes = instance.notes
            
            instance.refresh_from_db()
            
            # Restore field values after refresh
            instance.delivery_type = delivery_type
            instance.delivery_location = delivery_location
            instance.custom_delivery_location = custom_delivery_location
            instance.custom_delivery_fee = custom_delivery_fee
            instance.customer_phone = customer_phone
            instance.status = status
            instance.notes = notes
            
            # Recalculate delivery fee again after refresh
            instance.delivery_fee = instance._calculate_delivery_fee()
        
        logger.debug(f"Calculating total before saving order: {instance.id}")
        instance.calculate_total()  # Recalculate total price based on updated items and delivery_fee
        logger.debug(f"Total price calculated for order: {instance.id} is {instance.total_price}")
        
        # Save all the updated fields
        instance.save()
        return instance

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)

    class Meta:
        model = Order
        fields = ['status']

    def validate_status(self, value):
        """Validate status transitions based on order type and payment status"""
        order = self.instance
        payment_status = order.get_payment_status()
        is_payment_confirmed = payment_status in ['PAID', 'OVERPAID']
        
        # Special validation for "Out for Delivery" status
        if value == Order.STATUS_OUT_FOR_DELIVERY:
            # Check if order is a delivery order
            if order.delivery_type != 'Delivery':
                raise serializers.ValidationError(
                    'Out for Delivery status is only available for delivery orders.'
                )
            # No payment requirement for "Out for Delivery" - only delivery type check
        
        # Payment validation - only "Fulfilled" status requires payment for all order types
        if value == Order.STATUS_FULFILLED and not is_payment_confirmed:
            raise serializers.ValidationError(
                'Fulfilled status requires full payment. Current payment status: {}'
                .format(payment_status)
            )
        
        return value

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance

class DeliveryLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryLocation
        fields = ['id', 'name', 'fee', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
