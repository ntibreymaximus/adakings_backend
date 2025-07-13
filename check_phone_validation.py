import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from apps.orders.models import Order, DeliveryLocation
from apps.customers.models import Customer
from apps.branches.models import Branch
from django.core.exceptions import ValidationError
from datetime import datetime

def check_special_delivery_locations():
    """Check if Bolt and WIX delivery locations exist"""
    print("=== Checking Special Delivery Locations ===")
    
    bolt_delivery = DeliveryLocation.objects.filter(name="Bolt Delivery").first()
    wix_delivery = DeliveryLocation.objects.filter(name="WIX Delivery").first()
    
    if bolt_delivery:
        print(f"✓ Bolt Delivery exists - ID: {bolt_delivery.id}, Fee: {bolt_delivery.fee}, Active: {bolt_delivery.is_active}")
    else:
        print("✗ Bolt Delivery NOT found")
    
    if wix_delivery:
        print(f"✓ WIX Delivery exists - ID: {wix_delivery.id}, Fee: {wix_delivery.fee}, Active: {wix_delivery.is_active}")
    else:
        print("✗ WIX Delivery NOT found")
    
    print("\n=== All Delivery Locations ===")
    all_locations = DeliveryLocation.objects.all()
    for loc in all_locations:
        print(f"- {loc.name} (ID: {loc.id}, Fee: {loc.fee}, Active: {loc.is_active})")
    
    return bolt_delivery, wix_delivery

def test_order_creation_without_phone(delivery_location):
    """Test creating an order with special delivery location without phone"""
    print(f"\n=== Testing Order Creation with {delivery_location.name} (No Phone) ===")
    
    # Get first available customer and branch
    customer = Customer.objects.first()
    branch = Branch.objects.first()
    
    if not customer or not branch:
        print("✗ Cannot test - no customer or branch found in database")
        return False
    
    # Create test order
    test_order = Order(
        customer=customer,
        branch=branch,
        order_type='Regular',
        delivery_type='Delivery',
        delivery_location=delivery_location,
        customer_phone='',  # Empty phone number
        delivery_address='Test Address',
        total_amount=50.00,
        status='Pending'
    )
    
    try:
        # This will trigger the clean() method validation
        test_order.full_clean()
        print(f"✓ Validation passed! Order can be created without phone for {delivery_location.name}")
        return True
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
        return False

def test_regular_delivery_requires_phone():
    """Test that regular delivery still requires phone"""
    print("\n=== Testing Regular Delivery (Should Require Phone) ===")
    
    # Get first available customer, branch, and regular delivery location
    customer = Customer.objects.first()
    branch = Branch.objects.first()
    regular_location = DeliveryLocation.objects.exclude(
        name__in=["Bolt Delivery", "WIX Delivery"]
    ).first()
    
    if not customer or not branch or not regular_location:
        print("✗ Cannot test - missing required data")
        return
    
    # Create test order without phone
    test_order = Order(
        customer=customer,
        branch=branch,
        order_type='Regular',
        delivery_type='Delivery',
        delivery_location=regular_location,
        customer_phone='',  # Empty phone number
        delivery_address='Test Address',
        total_amount=50.00,
        status='Pending'
    )
    
    try:
        test_order.full_clean()
        print(f"✗ Unexpected: Regular delivery ({regular_location.name}) allowed without phone!")
    except ValidationError as e:
        if 'customer_phone' in str(e):
            print(f"✓ Correct: Regular delivery ({regular_location.name}) requires phone - {e}")
        else:
            print(f"✗ Unexpected error: {e}")

def main():
    """Main function to run all checks"""
    print("Phone Validation Check for Bolt/WIX Deliveries")
    print("=" * 50)
    
    # Check if special locations exist
    bolt_delivery, wix_delivery = check_special_delivery_locations()
    
    # Test order creation if locations exist
    if bolt_delivery:
        test_order_creation_without_phone(bolt_delivery)
    
    if wix_delivery:
        test_order_creation_without_phone(wix_delivery)
    
    # Test that regular delivery still requires phone
    test_regular_delivery_requires_phone()
    
    print("\n" + "=" * 50)
    print("Check completed!")

if __name__ == "__main__":
    main()
