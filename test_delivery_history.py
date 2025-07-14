#!/usr/bin/env python
"""
Test script to verify delivery history preservation after server restart
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from apps.orders.models import Order
from apps.deliveries.models import DeliveryLocation

def test_delivery_history():
    print("\n" + "="*60)
    print("DELIVERY HISTORY PRESERVATION TEST")
    print("="*60)
    
    # Check delivery locations
    print(f"\nDelivery Locations Count: {DeliveryLocation.objects.count()}")
    
    # Check orders with delivery
    delivery_orders = Order.objects.filter(delivery_type='Delivery')
    print(f"\nTotal Delivery Orders: {delivery_orders.count()}")
    
    # Check preservation
    preserved_count = 0
    missing_count = 0
    
    print("\nSample Orders:")
    print("-" * 60)
    
    for order in delivery_orders[:10]:
        has_fk = order.delivery_location is not None
        has_history = order.delivery_location_name is not None
        
        if has_history:
            preserved_count += 1
        else:
            missing_count += 1
            
        print(f"Order {order.order_number}:")
        print(f"  FK Present: {'Yes' if has_fk else 'No'}")
        print(f"  Historical Name: {order.delivery_location_name or 'MISSING'}")
        print(f"  Historical Fee: {order.delivery_location_fee or 'MISSING'}")
        print(f"  Calculated Fee: {order._calculate_delivery_fee()}")
        print()
    
    # Summary
    print("="*60)
    print(f"Orders with preserved history: {preserved_count}")
    print(f"Orders missing history: {missing_count}")
    
    if missing_count == 0:
        print("\n✓ SUCCESS: All orders have preserved delivery history!")
    else:
        print("\n✗ WARNING: Some orders are missing delivery history!")
    
    print("="*60)

if __name__ == "__main__":
    test_delivery_history()
