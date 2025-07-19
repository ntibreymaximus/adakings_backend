from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    DeliveryRider, OrderAssignment, DeliveryLocation
)
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer


class DeliveryRiderSerializer(serializers.ModelSerializer):
    """Serializer for DeliveryRider model"""
    can_accept_orders = serializers.ReadOnlyField()
    
    class Meta:
        model = DeliveryRider
        fields = [
            'id', 'name', 'phone', 'status', 'current_orders',
            'total_deliveries', 'today_deliveries', 'created_at',
            'updated_at', 'is_available', 'max_concurrent_orders',
            'can_accept_orders'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_deliveries', 'today_deliveries']


class DeliveryRiderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new delivery rider"""
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = DeliveryRider
        fields = ['name', 'phone', 'username', 'password']
    
    def create(self, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        
        # Create user account if username and password provided
        if username and password:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=validated_data.get('name', '').split()[0] if validated_data.get('name') else ''
            )
            validated_data['user'] = user
        
        return DeliveryRider.objects.create(**validated_data)


class OrderAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for OrderAssignment model"""
    order_details = OrderSerializer(source='order', read_only=True)
    rider_details = DeliveryRiderSerializer(source='rider', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderAssignment
        fields = [
            'id', 'order', 'rider', 'picked_up_at', 'delivered_at', 'status',
            'delivery_instructions', 'delivery_notes',
            'cancellation_reason', 'order_details', 'rider_details', 'duration'
        ]
        read_only_fields = [
            'picked_up_at', 'delivered_at'
        ]
    
    def get_duration(self, obj):
        """Calculate delivery duration"""
        if obj.delivered_at and obj.picked_up_at:
            duration = obj.delivered_at - obj.picked_up_at
            return {
                'minutes': int(duration.total_seconds() / 60),
                'formatted': str(duration)
            }
        return None


class AssignRiderSerializer(serializers.Serializer):
    """Serializer for assigning a rider to an order"""
    rider_id = serializers.IntegerField()
    delivery_instructions = serializers.CharField(required=False, allow_blank=True)
    
    def validate_rider_id(self, value):
        try:
            rider = DeliveryRider.objects.get(id=value)
            if not rider.can_accept_orders:
                raise serializers.ValidationError("This rider cannot accept orders at the moment.")
            return value
        except DeliveryRider.DoesNotExist:
            raise serializers.ValidationError("Rider not found.")


class UpdateAssignmentStatusSerializer(serializers.Serializer):
    """Serializer for updating assignment status"""
    status = serializers.ChoiceField(choices=[choice[0] for choice in OrderAssignment.STATUS_CHOICES])
    notes = serializers.CharField(required=False, allow_blank=True)
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)


class DeliveryLocationSerializer(serializers.ModelSerializer):
    """Serializer for DeliveryLocation model"""
    class Meta:
        model = DeliveryLocation
        fields = ['id', 'name', 'fee', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class RiderAvailabilitySerializer(serializers.Serializer):
    """Serializer for updating rider availability"""
    is_available = serializers.BooleanField()
    status = serializers.ChoiceField(choices=['active', 'busy', 'inactive'], required=False)


class DeliveryTrackingSerializer(serializers.Serializer):
    """Serializer for public delivery tracking"""
    order_number = serializers.CharField()
    status = serializers.CharField()
    rider_name = serializers.CharField()
    rider_phone = serializers.CharField()
    estimated_time = serializers.CharField(allow_null=True)
    current_location = serializers.DictField(allow_null=True)
    delivery_updates = serializers.ListField(child=serializers.DictField())
