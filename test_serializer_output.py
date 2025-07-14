#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer

# Get a sample order
order = Order.objects.filter(delivery_type='Delivery').first()

if order:
    print(f"\nTesting Order: {order.order_number}")
    print(f"Model Data:")
    print(f"  - delivery_location: {order.delivery_location}")
    print(f"  - delivery_location_name: {order.delivery_location_name}")
    print(f"  - delivery_location_fee: {order.delivery_location_fee}")
    print(f"  - get_effective_delivery_location_name(): {order.get_effective_delivery_location_name()}")
    
    # Serialize the order
    serializer = OrderSerializer(order)
    data = serializer.data
    
    print(f"\nSerialized Data:")
    print(f"  - delivery_location: {data.get('delivery_location')}")
    print(f"  - delivery_location_name: {data.get('delivery_location_name')}")
    print(f"  - delivery_location_fee: {data.get('delivery_location_fee')}")
    print(f"  - effective_delivery_location_name: {data.get('effective_delivery_location_name')}")
    
    print(f"\nFull delivery-related fields:")
    for key, value in data.items():
        if 'delivery' in key.lower():
            print(f"  - {key}: {value}")
else:
    print("No delivery orders found!")
