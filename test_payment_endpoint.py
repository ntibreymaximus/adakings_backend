#!/usr/bin/env python3
"""
Test script to debug the payment endpoint issue
"""
import os
import sys
import django
import json
from django.conf import settings

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.orders.models import Order
from apps.payments.serializers import PaymentInitiateSerializer

User = get_user_model()

def test_payment_endpoint():
    """Test the payment endpoint with minimal data"""
    
    # Create a test user if none exists
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("❌ No staff user found. Please create a user first.")
        return
    
    # Get an existing order or create one
    order = Order.objects.first()
    if not order:
        print("❌ No orders found. Please create an order first.")
        return
    
    print(f"✅ Found order: {order.order_number}")
    print(f"✅ Order total: {order.total_price}")
    print(f"✅ Order status: {order.status}")
    
    # Check delivery location requirements
    print(f"📍 Order delivery type: {getattr(order, 'delivery_type', 'N/A')}")
    if hasattr(order, 'delivery_type') and order.delivery_type == 'Delivery':
        delivery_location = getattr(order, 'delivery_location', None)
        custom_delivery_location = getattr(order, 'custom_delivery_location', None)
        
        print(f"📍 Delivery location: {delivery_location}")
        print(f"📍 Custom delivery location: {custom_delivery_location}")
        
        if not delivery_location and not custom_delivery_location:
            print("⚠️  WARNING: This is a delivery order but has no delivery_location or custom_delivery_location!")
            print("⚠️  This may cause payment validation to fail.")
        else:
            print("✅ Delivery location requirements satisfied")
    
    # Test data that matches the frontend
    test_data = {
        "order_number": str(order.order_number),
        "amount": float(order.total_price),
        "payment_method": "CASH",
        "payment_type": "payment"
    }
    
    print(f"📤 Testing with data: {json.dumps(test_data, indent=2)}")
    
    # Test the serializer directly
    print("\n🔍 Testing serializer validation:")
    try:
        serializer = PaymentInitiateSerializer(data=test_data)
        if serializer.is_valid():
            print("✅ Serializer validation passed")
            print(f"✅ Validated data: {serializer.validated_data}")
        else:
            print("❌ Serializer validation failed")
            print(f"❌ Errors: {serializer.errors}")
            return
    except Exception as e:
        print(f"❌ Serializer exception: {e}")
        return
    
    # Test the API endpoint
    print("\n🌐 Testing API endpoint:")
    client = Client()
    
    # Login the user
    client.force_login(user)
    
    try:
        response = client.post(
            '/api/payments/initiate/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ API call successful")
            try:
                response_data = json.loads(response.content.decode())
                print(f"✅ Response data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"✅ Response content: {response.content.decode()}")
        else:
            print("❌ API call failed")
            print(f"❌ Response content: {response.content.decode()}")
            
    except Exception as e:
        print(f"❌ API exception: {e}")

if __name__ == "__main__":
    test_payment_endpoint()
