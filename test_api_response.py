#!/usr/bin/env python3
import os
import sys
import django
import json

# Add the Django project to the Python path
sys.path.append('.')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

def test_api_response():
    """Test API response structure for historical data"""
    print("Testing API response structure for historical data...")
    
    # Get some recent orders
    orders = Order.objects.filter(delivery_type='Delivery').select_related('delivery_location')[:3]
    
    print(f"Found {orders.count()} delivery orders to test")
    
    for order in orders:
        print(f"\n--- Testing API Response for Order {order.order_number} ---")
        
        # Create a test client
        client = APIClient()
        
        # Create a test user for authentication
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'password': 'testpass123',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Authenticate the client
        client.force_authenticate(user=user)
        
        # Make API call
        response = client.get(f'/api/orders/{order.order_number}/')
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check historical data fields
            print(f"Historical data in API response:")
            print(f"  delivery_location: {data.get('delivery_location')}")
            print(f"  delivery_location_name: {data.get('delivery_location_name')}")
            print(f"  delivery_location_fee: {data.get('delivery_location_fee')}")
            print(f"  custom_delivery_location: {data.get('custom_delivery_location')}")
            print(f"  custom_delivery_fee: {data.get('custom_delivery_fee')}")
            print(f"  effective_delivery_location_name: {data.get('effective_delivery_location_name')}")
            
            # Check if historical data is properly populated
            has_historical_data = (
                data.get('delivery_location_name') or 
                data.get('custom_delivery_location')
            )
            
            if has_historical_data:
                print(f"  ✅ Historical data properly exposed in API")
            else:
                print(f"  ❌ Missing historical data in API response")
                
            # Check if effective delivery location name is working
            if data.get('effective_delivery_location_name'):
                print(f"  ✅ Effective delivery location name: {data.get('effective_delivery_location_name')}")
            else:
                print(f"  ❌ Missing effective delivery location name")
                
        else:
            print(f"  ❌ API call failed with status {response.status_code}")
            print(f"  Response: {response.content}")

if __name__ == "__main__":
    test_api_response()
