from django.core.management.base import BaseCommand
from apps.orders.models import Order
from django.db import transaction


class Command(BaseCommand):
    help = 'Ensure all orders have historical delivery location data populated'

    def handle(self, *args, **options):
        self.stdout.write("Checking orders for missing historical delivery data...")
        
        # Find orders with delivery location but missing historical data
        orders_missing_history = Order.objects.filter(
            delivery_location__isnull=False,
            delivery_location_name__isnull=True
        ).select_related('delivery_location')
        
        count = orders_missing_history.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("All orders have historical delivery data!"))
            return
        
        self.stdout.write(f"Found {count} orders missing historical data. Updating...")
        
        updated = 0
        with transaction.atomic():
            for order in orders_missing_history:
                if order.delivery_location:
                    order.delivery_location_name = order.delivery_location.name
                    order.delivery_location_fee = order.delivery_location.fee
                    order.save(update_fields=['delivery_location_name', 'delivery_location_fee'])
                    updated += 1
        
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated} orders with historical data"))
        
        # Also check for custom delivery locations
        custom_orders = Order.objects.filter(
            custom_delivery_location__isnull=False,
            delivery_location__isnull=True,
            delivery_location_name__isnull=True
        )
        
        if custom_orders.exists():
            self.stdout.write(f"Found {custom_orders.count()} orders with custom locations...")
            custom_updated = 0
            
            with transaction.atomic():
                for order in custom_orders:
                    order.delivery_location_name = order.custom_delivery_location
                    order.delivery_location_fee = order.custom_delivery_fee
                    order.save(update_fields=['delivery_location_name', 'delivery_location_fee'])
                    custom_updated += 1
            
            self.stdout.write(self.style.SUCCESS(f"Updated {custom_updated} custom location orders"))
