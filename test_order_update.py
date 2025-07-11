#!/usr/bin/env python
"""
Test script to verify order update total calculation
Run this from the backend directory: python test_order_update.py
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from apps.orders.models import Order, OrderItem
from decimal import Decimal

def test_order_update():
    """Test that order total is correctly calculated after update"""
    try:
        # Get the order we've been testing
        order = Order.objects.get(order_number="110725-007")
        
        print(f"Order Number: {order.order_number}")
        print(f"Before update - Total Price: {order.total_price}")
        print(f"Delivery Fee: {order.delivery_fee}")
        
        # Get all items and calculate expected total
        items = order.items.all()
        items_subtotal = sum(item.calculate_subtotal() for item in items)
        expected_total = items_subtotal + order.delivery_fee
        
        print(f"Items subtotal: {items_subtotal}")
        print(f"Expected total (items + delivery): {expected_total}")
        
        # Force recalculation
        order.calculate_total()
        order.save()
        
        print(f"After recalculation - Total Price: {order.total_price}")
        
        # Verify the total is correct
        if order.total_price == expected_total:
            print("✅ Total calculation is CORRECT!")
        else:
            print("❌ Total calculation is INCORRECT!")
            print(f"Expected: {expected_total}, Got: {order.total_price}")
            
        # Show item details
        print("\nItem Details:")
        for item in items:
            print(f"  - {item.menu_item.name}: {item.quantity} x ₵{item.unit_price} = ₵{item.subtotal}")
            
    except Order.DoesNotExist:
        print("Order 110725-007 not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_order_update()
