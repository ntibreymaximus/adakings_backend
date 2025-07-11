#!/usr/bin/env python
"""
Test delivery fee changes specifically
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from apps.orders.models import Order, OrderItem, DeliveryLocation
from apps.orders.serializers import OrderSerializer
from decimal import Decimal

def test_delivery_fee_only():
    """Test delivery fee changes specifically"""
    try:
        # Get the order
        order = Order.objects.get(order_number="110725-007")
        
        print("=" * 60)
        print("DELIVERY FEE SPECIFIC TEST")
        print("=" * 60)
        
        print(f"\nInitial State:")
        print(f"Delivery Type: {order.delivery_type}")
        print(f"Delivery Location: {order.delivery_location}")
        print(f"Delivery Fee: {order.delivery_fee}")
        print(f"Total Price: {order.total_price}")
        
        # Test 1: Change to Pickup
        print(f"\n{'='*40}")
        print("TEST 1: Change to Pickup")
        print(f"{'='*40}")
        
        update_data = {
            'delivery_type': 'Pickup',
            'delivery_location': None,
            'items': [
                {'menu_item_id': item.menu_item.id, 'quantity': item.quantity}
                for item in order.items.all()
            ]
        }
        
        print(f"Update data: {update_data}")
        
        serializer = OrderSerializer(order, data=update_data, partial=True)
        if serializer.is_valid():
            updated_order = serializer.save()
            print(f"✅ Successfully updated to Pickup")
            print(f"New Delivery Type: {updated_order.delivery_type}")
            print(f"New Delivery Location: {updated_order.delivery_location}")
            print(f"New Delivery Fee: {updated_order.delivery_fee}")
            print(f"New Total Price: {updated_order.total_price}")
            
            # Manual calculation check
            manual_fee = updated_order._calculate_delivery_fee()
            print(f"Manual calculation delivery fee: {manual_fee}")
            
        else:
            print(f"❌ Validation failed: {serializer.errors}")
            
        # Test 2: Change back to Delivery
        print(f"\n{'='*40}")
        print("TEST 2: Change back to Delivery")
        print(f"{'='*40}")
        
        delivery_location = DeliveryLocation.objects.filter(is_active=True).first()
        update_data = {
            'delivery_type': 'Delivery',
            'delivery_location': delivery_location.id,
            'customer_phone': '0555123456',
            'items': [
                {'menu_item_id': item.menu_item.id, 'quantity': item.quantity}
                for item in order.items.all()
            ]
        }
        
        print(f"Update data: {update_data}")
        
        serializer = OrderSerializer(order, data=update_data, partial=True)
        if serializer.is_valid():
            updated_order = serializer.save()
            print(f"✅ Successfully updated to Delivery")
            print(f"New Delivery Type: {updated_order.delivery_type}")
            print(f"New Delivery Location: {updated_order.delivery_location}")
            print(f"New Delivery Fee: {updated_order.delivery_fee}")
            print(f"New Total Price: {updated_order.total_price}")
            
            # Manual calculation check
            manual_fee = updated_order._calculate_delivery_fee()
            print(f"Manual calculation delivery fee: {manual_fee}")
            
        else:
            print(f"❌ Validation failed: {serializer.errors}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_delivery_fee_only()
