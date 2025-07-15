#!/usr/bin/env python3
import os
import sys
import django

# Add the Django project to the Python path
sys.path.append('.')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
from django.db import transaction
import json

def test_historical_data():
    """Test historical data synchronization"""
    print("Testing historical data synchronization...")
    
    # Get some recent orders
    orders = Order.objects.filter(delivery_type='Delivery').select_related('delivery_location')[:5]
    
    print(f"Found {orders.count()} delivery orders to test")
    
    for order in orders:
        print(f"\n--- Testing Order {order.order_number} ---")
        
        # Check model fields
        print(f"Model data:")
        print(f"  delivery_location: {order.delivery_location}")
        print(f"  delivery_location_name: {order.delivery_location_name}")
        print(f"  delivery_location_fee: {order.delivery_location_fee}")
        print(f"  custom_delivery_location: {order.custom_delivery_location}")
        print(f"  custom_delivery_fee: {order.custom_delivery_fee}")
        print(f"  effective_delivery_location_name: {order.get_effective_delivery_location_name()}")
        
        # Check serializer output
        serializer = OrderSerializer(order)
        serialized_data = serializer.data
        
        print(f"Serialized data:")
        print(f"  delivery_location: {serialized_data.get('delivery_location')}")
        print(f"  delivery_location_name: {serialized_data.get('delivery_location_name')}")
        print(f"  delivery_location_fee: {serialized_data.get('delivery_location_fee')}")
        print(f"  custom_delivery_location: {serialized_data.get('custom_delivery_location')}")
        print(f"  custom_delivery_fee: {serialized_data.get('custom_delivery_fee')}")
        print(f"  effective_delivery_location_name: {serialized_data.get('effective_delivery_location_name')}")
        
        # Check for missing historical data
        if not order.delivery_location_name and not order.custom_delivery_location:
            print(f"  ⚠️  WARNING: Order {order.order_number} has no historical location data!")
        elif not order.delivery_location_name and order.delivery_location:
            print(f"  ⚠️  WARNING: Order {order.order_number} has delivery_location but no historical name!")
        else:
            print(f"  ✅ Historical data looks good")

if __name__ == "__main__":
    test_historical_data()
