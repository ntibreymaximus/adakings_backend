import os
import django

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fooddelivery.settings')
django.setup()

from myapp.models import Order, DeliveryLocation

# Check for Bolt and WIX delivery locations
print("=== Checking Delivery Locations ===")
bolt_location = DeliveryLocation.objects.filter(name__icontains="Bolt").first()
wix_location = DeliveryLocation.objects.filter(name__icontains="WIX").first()

if bolt_location:
    print(f"Bolt Delivery Location found: {bolt_location.name} (ID: {bolt_location.id})")
else:
    print("No Bolt Delivery Location found")

if wix_location:
    print(f"WIX Delivery Location found: {wix_location.name} (ID: {wix_location.id})")
else:
    print("No WIX Delivery Location found")

print("\n=== Checking Orders ===")

# Check orders with Bolt delivery
if bolt_location:
    bolt_orders = Order.objects.filter(delivery_location=bolt_location).order_by('-created_at')[:5]
    print(f"\nLatest 5 Bolt orders (Total: {Order.objects.filter(delivery_location=bolt_location).count()}):")
    for order in bolt_orders:
        print(f"  Order #{order.id}: Customer Phone: '{order.customer_phone}', Created: {order.created_at}")

# Check orders with WIX delivery
if wix_location:
    wix_orders = Order.objects.filter(delivery_location=wix_location).order_by('-created_at')[:5]
    print(f"\nLatest 5 WIX orders (Total: {Order.objects.filter(delivery_location=wix_location).count()}):")
    for order in wix_orders:
        print(f"  Order #{order.id}: Customer Phone: '{order.customer_phone}', Created: {order.created_at}")

# Check if there are any orders with empty customer phone for these locations
print("\n=== Phone Number Analysis ===")
if bolt_location:
    bolt_empty_phone = Order.objects.filter(delivery_location=bolt_location, customer_phone='').count()
    bolt_null_phone = Order.objects.filter(delivery_location=bolt_location, customer_phone__isnull=True).count()
    print(f"Bolt orders with empty phone: {bolt_empty_phone}")
    print(f"Bolt orders with null phone: {bolt_null_phone}")

if wix_location:
    wix_empty_phone = Order.objects.filter(delivery_location=wix_location, customer_phone='').count()
    wix_null_phone = Order.objects.filter(delivery_location=wix_location, customer_phone__isnull=True).count()
    print(f"WIX orders with empty phone: {wix_empty_phone}")
    print(f"WIX orders with null phone: {wix_null_phone}")
