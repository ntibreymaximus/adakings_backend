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
from apps.deliveries.models import DeliveryLocation
from apps.menu.models import MenuItem
from decimal import Decimal
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

def test_delivery_order_validation():
    """Test different scenarios for delivery order validation"""
    
    print("Testing Delivery Order Validation Scenarios")
    print("=" * 60)
    
    # Get available delivery locations
    locations = DeliveryLocation.objects.filter(is_active=True)
    print(f"\nAvailable Delivery Locations:")
    for loc in locations:
        print(f"  - {loc.name} (ID: {loc.id}, Fee: ₵{loc.fee})")
    
    # Get a valid menu item
    menu_item = MenuItem.objects.filter(is_available=True, item_type='regular').first()
    if not menu_item:
        print("\nNo available menu items found! Creating a test item...")
        # Create a test menu item
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'password')
        menu_item = MenuItem.objects.create(
            name="Test Item",
            item_type='regular',
            price=Decimal("10.00"),
            is_available=True,
            created_by=admin_user
        )
    print(f"\nUsing menu item: {menu_item.name} (ID: {menu_item.id})")
    
    # Test scenarios
    test_cases = [
        {
            "name": "Valid delivery with location ID",
            "data": {
                "delivery_type": "Delivery",
                "delivery_location": locations.first().id if locations.exists() else None,
                "customer_phone": "+233123456789",
                "items": [{"menu_item_id": menu_item.id, "quantity": 1, "price": str(menu_item.price)}]
            }
        },
        {
            "name": "Valid delivery with custom location",
            "data": {
                "delivery_type": "Delivery",
                "custom_delivery_location": "Custom Location Name",
                "custom_delivery_fee": "5.00",
                "customer_phone": "+233123456789",
                "items": [{"menu_item_id": menu_item.id, "quantity": 1, "price": str(menu_item.price)}]
            }
        },
        {
            "name": "Missing both location and custom location",
            "data": {
                "delivery_type": "Delivery",
                "customer_phone": "+233123456789",
                "items": [{"menu_item_id": menu_item.id, "quantity": 1, "price": str(menu_item.price)}]
            }
        },
        {
            "name": "Missing phone for delivery",
            "data": {
                "delivery_type": "Delivery",
                "delivery_location": locations.first().id if locations.exists() else None,
                "items": [{"menu_item_id": menu_item.id, "quantity": 1, "price": str(menu_item.price)}]
            }
        },
        {
            "name": "Both location and custom location provided",
            "data": {
                "delivery_type": "Delivery",
                "delivery_location": locations.first().id if locations.exists() else None,
                "custom_delivery_location": "Custom Location",
                "custom_delivery_fee": "5.00",
                "customer_phone": "+233123456789",
                "items": [{"menu_item_id": menu_item.id, "quantity": 1, "price": str(menu_item.price)}]
            }
        },
        {
            "name": "Custom location without fee",
            "data": {
                "delivery_type": "Delivery",
                "custom_delivery_location": "Custom Location",
                "customer_phone": "+233123456789",
                "items": [{"menu_item_id": menu_item.id, "quantity": 1, "price": str(menu_item.price)}]
            }
        },
        {
            "name": "Bolt delivery (no phone required)",
            "data": {
                "delivery_type": "Delivery",
                "delivery_location": next((loc.id for loc in locations if loc.name == "Bolt Delivery"), None),
                "items": [{"menu_item_id": menu_item.id, "quantity": 1, "price": str(menu_item.price)}]
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Test: {test_case['name']} ---")
        print(f"Data: {json.dumps(test_case['data'], indent=2)}")
        
        try:
            # Test with serializer
            serializer = OrderSerializer(data=test_case['data'])
            
            if serializer.is_valid():
                print("✅ Serializer validation: PASSED")
                print(f"Validated data: {json.dumps(serializer.validated_data, indent=2, default=str)}")
            else:
                print("❌ Serializer validation: FAILED")
                print(f"Errors: {json.dumps(serializer.errors, indent=2)}")
                
        except Exception as e:
            print(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")
            
    # Test model-level validation
    print("\n\n--- Testing Model-Level Validation ---")
    
    # Test creating an order with missing delivery location
    print("\nCreating delivery order without location:")
    try:
        order = Order(
            delivery_type="Delivery",
            customer_phone="+233123456789"
        )
        order.full_clean()
        print("❌ Model validation passed (should have failed)")
    except DjangoValidationError as e:
        print("✅ Model validation failed as expected:")
        print(f"   {e}")
        
    # Test creating an order with custom location
    print("\nCreating delivery order with custom location:")
    try:
        order = Order(
            delivery_type="Delivery",
            customer_phone="+233123456789",
            custom_delivery_location="Test Location",
            custom_delivery_fee=Decimal("5.00")
        )
        order.full_clean()
        print("✅ Model validation passed")
    except DjangoValidationError as e:
        print("❌ Model validation failed:")
        print(f"   {e}")

if __name__ == "__main__":
    test_delivery_order_validation()
