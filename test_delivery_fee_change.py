#!/usr/bin/env python
"""
Test script to verify delivery fee calculation when delivery type changes
Run this from the backend directory: python test_delivery_fee_change.py
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
from decimal import Decimal

def test_delivery_fee_change():
    """Test that delivery fee changes correctly when delivery type changes"""
    try:
        # Get the order we've been testing
        order = Order.objects.get(order_number="110725-007")
        
        print(f"Order Number: {order.order_number}")
        print(f"Current Delivery Type: {order.delivery_type}")
        print(f"Current Delivery Fee: {order.delivery_fee}")
        print(f"Current Total Price: {order.total_price}")
        
        # Get all items and calculate expected total
        items = order.items.all()
        items_subtotal = sum(item.calculate_subtotal() for item in items)
        print(f"Items subtotal: {items_subtotal}")
        
        # Test changing from current type to opposite
        if order.delivery_type == "Pickup":
            # Change to Delivery - need to set a delivery location
            delivery_location = DeliveryLocation.objects.filter(is_active=True).first()
            if delivery_location:
                order.delivery_type = "Delivery"
                order.delivery_location = delivery_location
                order.customer_phone = "0555123456"  # Required for delivery
                print(f"\\nChanging to Delivery (location: {delivery_location.name}, fee: {delivery_location.fee})")
            else:
                print("No active delivery locations found")
                return
        else:
            # Change to Pickup
            order.delivery_type = "Pickup"
            order.delivery_location = None
            order.custom_delivery_location = None
            order.custom_delivery_fee = None
            print(f"\\nChanging to Pickup")
        
        # Manually calculate delivery fee
        old_delivery_fee = order.delivery_fee
        order.delivery_fee = order._calculate_delivery_fee()
        print(f"Delivery fee changed from {old_delivery_fee} to {order.delivery_fee}")
        
        # Recalculate total
        order.calculate_total()
        print(f"New total price: {order.total_price}")
        
        # Expected total
        expected_total = items_subtotal + order.delivery_fee
        print(f"Expected total (items + delivery): {expected_total}")
        
        # Save the changes
        order.save()
        print("Changes saved successfully!")
        
        # Verify the total is correct
        if order.total_price == expected_total:
            print("✅ Delivery fee and total calculation are CORRECT!")
        else:
            print("❌ Delivery fee and total calculation are INCORRECT!")
            print(f"Expected: {expected_total}, Got: {order.total_price}")
            
    except Order.DoesNotExist:
        print("Order 110725-007 not found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_delivery_fee_change()
