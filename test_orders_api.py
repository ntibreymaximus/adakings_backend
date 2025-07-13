#!/usr/bin/env python
"""
Test script to debug the /api/orders/ endpoint 400 Bad Request error.
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.users.models import CustomUser

# API configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
ORDERS_URL = f"{BASE_URL}/api/orders/"

def get_auth_token():
    """Get authentication token for testing."""
    # Try to login with a test user
    print("Attempting to login...")
    
    # First, let's check if we have any users
    users = CustomUser.objects.all()
    if not users.exists():
        print("No users found in database. Creating a test user...")
        user = CustomUser.objects.create_superuser(
            email='admin@test.com',
            password='admin123',
            first_name='Test',
            last_name='Admin'
        )
        print(f"Created test user: {user.email}")
        credentials = {'email': 'admin@test.com', 'password': 'admin123'}
    else:
        # Use the first available user
        user = users.first()
        print(f"Found existing user: {user.email}")
        print("Please use the login endpoint manually to get a token.")
        return None
    
    # Try to login
    response = requests.post(LOGIN_URL, json=credentials)
    if response.status_code == 200:
        data = response.json()
        return data.get('access')
    else:
        print(f"Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_orders_endpoint():
    """Test the orders endpoint to identify the 400 error cause."""
    print("\n" + "="*50)
    print("Testing /api/orders/ endpoint")
    print("="*50 + "\n")
    
    # Test 1: Without authentication
    print("Test 1: GET request without authentication")
    response = requests.get(ORDERS_URL)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("\nCould not obtain auth token. Please check authentication.")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test 2: With authentication
    print("\n\nTest 2: GET request with authentication")
    response = requests.get(ORDERS_URL, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Orders retrieved.")
        data = response.json()
        print(f"Number of orders: {data.get('count', len(data))}")
    else:
        print(f"Response: {response.text}")
    
    # Test 3: POST request with minimal data
    print("\n\nTest 3: POST request with minimal data")
    minimal_order = {
        "delivery_type": "Pickup",
        "items": [{
            "menu_item_id": 1,  # This might fail if menu item doesn't exist
            "quantity": 1
        }]
    }
    response = requests.post(ORDERS_URL, json=minimal_order, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 4: POST request with more complete data
    print("\n\nTest 4: POST request with complete data")
    complete_order = {
        "customer_phone": "0551234567",
        "delivery_type": "Delivery",
        "delivery_location": "Adabraka",  # This needs to be a valid location
        "items": [{
            "menu_item_id": 1,
            "quantity": 2,
            "notes": "Extra spicy"
        }],
        "notes": "Test order"
    }
    response = requests.post(ORDERS_URL, json=complete_order, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 5: Check available delivery locations
    print("\n\nTest 5: Checking available delivery locations")
    locations_url = f"{BASE_URL}/api/orders/delivery-locations/"
    response = requests.get(locations_url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        locations = response.json()
        print(f"Available locations: {[loc['name'] for loc in locations]}")
    
    # Test 6: Check available menu items
    print("\n\nTest 6: Checking available menu items")
    menu_url = f"{BASE_URL}/api/menu/items/"
    response = requests.get(menu_url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        items = response.json()
        if items:
            print(f"Sample menu items: {[(item['id'], item['name']) for item in items[:3]]}")

if __name__ == "__main__":
    test_orders_endpoint()
