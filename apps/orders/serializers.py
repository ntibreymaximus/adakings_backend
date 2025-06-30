
# In adakings_backend/apps/orders/serializers.py

# Ensure these imports are present
from decimal import Decimal
from rest_framework import serializers
from apps.menu.models import MenuItem
from .models import Order, OrderItem, DeliveryLocation # OrderItem model no longer has parent_item

class DeliveryLocationField(serializers.Field):
    """Custom field that accepts either DeliveryLocation ID or name"""
    
    def to_representation(self, value):
        """Convert DeliveryLocation instance to its name for serialization"""
        if value is None:
            return None
        return value.name
    
    def to_internal_value(self, data):
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
    payment_status = serializers.SerializerMethodField()
    payment_mode = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    delivery_location = DeliveryLocationField(allow_null=True, required=False)
    delivery_location_name = serializers.CharField(source='delivery_location.name', read_only=True)
    delivery_location_fee = serializers.DecimalField(source='delivery_location.fee', max_digits=6, decimal_places=2, read_only=True)
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_phone',
            'delivery_type', 'delivery_location', 'delivery_location_name', 'delivery_location_fee',
            'status', 'total_price', 'delivery_fee', 'notes', 'created_at', 'updated_at',
            'items', 'amount_paid', 'balance_due', 'amount_overpaid', 
            'payment_status', 'payment_mode', 'payments', 'time_ago'
        ]
        read_only_fields = ['order_number', 'total_price', 'created_at', 'updated_at']
        extra_kwargs = {
            'customer_phone': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    
    def validate(self, data):
        """
        Validate that customer phone is provided when delivery is selected.
        """
        delivery_type = data.get('delivery_type', self.instance.delivery_type if self.instance else 'Pickup')
        customer_phone = data.get('customer_phone', self.instance.customer_phone if self.instance else None)
        delivery_location = data.get('delivery_location', self.instance.delivery_location if self.instance else None)
        
        if delivery_type == 'Delivery':
            errors = {}
            
            # Check customer phone
            if not customer_phone or customer_phone.strip() == '':
                errors['customer_phone'] = ['Customer phone number is required for delivery orders.']
            
            # Check delivery location
            if not delivery_location:
                errors['delivery_location'] = ['Delivery location is required for delivery orders.']
            
            if errors:
                raise serializers.ValidationError(errors)
        
        return data
    
    def get_payment_status(self, obj):
        """Get the payment status based on related payments"""
        return obj.get_payment_status()
    
    def get_payment_mode(self, obj):
        """Get the most recent payment method used"""
        latest_payment = obj.payments.filter(
            status='completed',
            payment_type='payment'
        ).order_by('-created_at').first()
        
        if latest_payment:
            return latest_payment.payment_method
        return None
    
    def get_payments(self, obj):
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
    
    def get_time_ago(self, obj):
        """Get the time since the order was last updated"""
        return obj.time_ago()

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        order.calculate_total() # Recalculate total after items are added
        order.save() # Save again to store the new total
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update Order instance fields
        instance.customer_phone = validated_data.get('customer_phone', instance.customer_phone)
        instance.delivery_type = validated_data.get('delivery_type', instance.delivery_type)
        instance.delivery_location = validated_data.get('delivery_location', instance.delivery_location)
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
        
        instance.delivery_fee = instance._calculate_delivery_fee() # Recalculate delivery fee based on potentially new location/type
        instance.calculate_total()  # Recalculate total price based on updated items and delivery_fee
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
        
        # Payment validation based on order type
        if order.delivery_type == 'Delivery':
            # For delivery orders: payment only required for "Fulfilled" status
            if value == Order.STATUS_FULFILLED and not is_payment_confirmed:
                raise serializers.ValidationError(
                    'Fulfilled status requires full payment for delivery orders. Current payment status: {}'
                    .format(payment_status)
                )
        else:
            # For pickup orders: payment required for Accepted and Fulfilled statuses (simplified workflow)
            restricted_statuses = [Order.STATUS_ACCEPTED, Order.STATUS_FULFILLED]
            if value in restricted_statuses and not is_payment_confirmed:
                raise serializers.ValidationError(
                    'Payment is required for {} status in pickup orders. Current payment status: {}'
                    .format(value, payment_status)
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
