#!/usr/bin/env python
"""
Comprehensive test for order editing scenarios
Run this from the backend directory: python test_order_editing.py
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

def test_order_editing_scenarios():
    """Test various order editing scenarios"""
    try:
        # Get the order we've been testing
        order = Order.objects.get(order_number="110725-007")
        
        print("=" * 60)
        print("COMPREHENSIVE ORDER EDITING TEST")
        print("=" * 60)
        
        print(f"\\nInitial Order State:")
        print(f"Order Number: {order.order_number}")
        print(f"Delivery Type: {order.delivery_type}")
        print(f"Delivery Fee: {order.delivery_fee}")
        print(f"Total Price: {order.total_price}")
        
        # Test 1: Change delivery type from Pickup to Delivery
        print(f"\\n{'='*40}")
        print("TEST 1: Change Pickup to Delivery")
        print(f"{'='*40}")
        
        delivery_location = DeliveryLocation.objects.filter(is_active=True).first()
        if not delivery_location:
            print("No active delivery locations found")
            return
            
        # Simulate frontend data for order update
        update_data = {
            'delivery_type': 'Delivery',
            'delivery_location': delivery_location.id,
            'customer_phone': '0555123456',
            'items': [
                {'menu_item_id': item.menu_item.id, 'quantity': item.quantity}
                for item in order.items.all()
            ]
        }
        
        serializer = OrderSerializer(order, data=update_data, partial=True)
        if serializer.is_valid():
            updated_order = serializer.save()
            print(f"✅ Successfully updated to Delivery")
            print(f"New Delivery Fee: {updated_order.delivery_fee}")
            print(f"New Total Price: {updated_order.total_price}")
            
            # Verify calculation
            items_subtotal = sum(item.calculate_subtotal() for item in updated_order.items.all())
            expected_total = items_subtotal + updated_order.delivery_fee
            if updated_order.total_price == expected_total:
                print(f"✅ Calculation is correct")
            else:
                print(f"❌ Calculation is incorrect. Expected: {expected_total}, Got: {updated_order.total_price}")
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
            
        # Test 2: Change delivery type from Delivery to Pickup
        print(f"\\n{'='*40}")
        print("TEST 2: Change Delivery to Pickup")
        print(f"{'='*40}")
        
        update_data = {
            'delivery_type': 'Pickup',
            'delivery_location': None,
            'items': [
                {'menu_item_id': item.menu_item.id, 'quantity': item.quantity}
                for item in order.items.all()
            ]
        }
        
        serializer = OrderSerializer(order, data=update_data, partial=True)
        if serializer.is_valid():
            updated_order = serializer.save()
            print(f"✅ Successfully updated to Pickup")
            print(f"New Delivery Fee: {updated_order.delivery_fee}")
            print(f"New Total Price: {updated_order.total_price}")
            
            # Verify calculation
            items_subtotal = sum(item.calculate_subtotal() for item in updated_order.items.all())
            expected_total = items_subtotal + updated_order.delivery_fee
            if updated_order.total_price == expected_total:
                print(f"✅ Calculation is correct")
            else:
                print(f"❌ Calculation is incorrect. Expected: {expected_total}, Got: {updated_order.total_price}")
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
            
        print(f"\\n{'='*60}")
        print("ALL TESTS COMPLETED")
        print(f"{'='*60}")
            
    except Order.DoesNotExist:
        print("Order 110725-007 not found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_order_editing_scenarios()
