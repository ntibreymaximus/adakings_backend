from rest_framework import serializers
from .models import Order
from .serializers import OrderSerializer
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class BoltOrderSerializer(OrderSerializer):
    """
    Special serializer for Bolt orders.
    These orders:
    1. Are already paid
    2. Have initial status: Bolt-Delivery
    3. Can be updated to: Fulfilled or Cancelled
    4. Don't require customer phone
    """
    
    class Meta(OrderSerializer.Meta):
        model = Order
        fields = OrderSerializer.Meta.fields
    
    def validate_status(self, value):
        """Ensure only valid statuses for Bolt orders"""
        # Allowed status transitions
        allowed_transitions = [Order.STATUS_ACCEPTED, Order.STATUS_FULFILLED, Order.STATUS_CANCELLED]
        
        # Only allow transitions to Accepted, Fulfilled, or Cancelled
        if value not in allowed_transitions:
            raise serializers.ValidationError(
                f"Bolt orders can only have status: {', '.join(allowed_transitions)}"
            )
        return value
    
    def validate(self, data):
        """Override parent validation to handle Bolt specific rules"""
        # Get delivery location
        delivery_location = data.get('delivery_location', self.instance.delivery_location if self.instance else None)
        
        # Check if this is actually a Bolt order
        if delivery_location and hasattr(delivery_location, 'name'):
            if delivery_location.name != "Bolt Delivery":
                raise serializers.ValidationError(
                    "This serializer is only for Bolt orders. Use regular OrderSerializer for other orders."
                )
        
        # Bypass parent's phone validation by calling grandparent's validate
        # This avoids the customer phone requirement
        validated_data = super(OrderSerializer, self).validate(data)
        
        # Validate status if provided
        if 'status' in data:
            self.validate_status(data['status'])
        
        return validated_data
    
    def create(self, validated_data):
        """Create a Bolt order with special handling"""
        # Status is automatically set by the Order model based on delivery location
        # No need to set it here
        
        # Create the order using parent's create method
        order = super().create(validated_data)
        
        # Log that this is a pre-paid Bolt order
        logger.info(f"Created {order.delivery_location.name} order {order.order_number} with status {order.status}")
        
        return order
    
    def update(self, instance, validated_data):
        """Update a Bolt order with restricted status changes"""
        # If status is being updated, validate it
        if 'status' in validated_data:
            self.validate_status(validated_data['status'])
        
        return super().update(instance, validated_data)
