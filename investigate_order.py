#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from apps.orders.models import Order
from apps.deliveries.models import OrderAssignment

def investigate_order():
    print("=== Order Investigation ===")
    
    # Check if order exists
    order = Order.objects.filter(order_number='120725-019').first()
    if order:
        print(f"Order: {order.order_number}")
        print(f"Status: {order.status}")
        print(f"Delivery Type: {order.delivery_type}")
        print(f"Customer Phone: {order.customer_phone}")
        print(f"Created: {order.created_at}")
        print(f"Updated: {order.updated_at}")
        
        # Check assignment
        assignment = OrderAssignment.objects.filter(order=order).first()
        if assignment:
            print(f"\nAssignment Status: {assignment.status}")
            print(f"Rider: {assignment.rider.name if assignment.rider else 'No rider'}")
            print(f"Picked up at: {assignment.picked_up_at}")
            print(f"Delivered at: {assignment.delivered_at}")
        else:
            print("\nNo assignment found for this order")
    else:
        print("Order not found")
        
        # Look for similar order numbers
        similar_orders = Order.objects.filter(order_number__icontains='120225').order_by('-created_at')
        print(f"\nSimilar orders found: {similar_orders.count()}")
        for order in similar_orders[:5]:
            print(f"  {order.order_number} - {order.status}")

if __name__ == "__main__":
    investigate_order()
