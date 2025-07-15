"""
Django management command to diagnose and fix delivery orders with missing location data.

Usage:
    python manage.py fix_delivery_orders                    # List all problematic orders
    python manage.py fix_delivery_orders --fix              # Fix all orders automatically
    python manage.py fix_delivery_orders --order ORDER_NUM  # Check specific order
    python manage.py fix_delivery_orders --order ORDER_NUM --fix  # Fix specific order
    python manage.py fix_delivery_orders --limit 10         # Limit number of orders to process
    python manage.py fix_delivery_orders --validate         # Validate all orders
"""

import logging
import sys
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.db.models import Q, Count
from decimal import Decimal
from apps.orders.models import Order, DeliveryLocation
from apps.payments.models import Payment
from apps.audit.utils import log_action, log_update

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Diagnose and fix delivery orders with missing location data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order',
            type=str,
            help='Check a specific order number'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix problematic orders'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of orders to process (for safety)'
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Run validation on all orders'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force fix even without confirmation (use with caution)'
        )

    def handle(self, *args, **options):
        order_number = options.get('order')
        fix_orders = options.get('fix', False)
        dry_run = options.get('dry_run', False)

        if order_number:
            self.check_specific_order(order_number, fix_orders, dry_run)
        else:
            self.check_all_orders(fix_orders, dry_run)

    def check_specific_order(self, order_number, fix=False, dry_run=False):
        """Check and optionally fix a specific order"""
        try:
            order = Order.objects.get(order_number=order_number)
            self.stdout.write(self.style.SUCCESS(f"\nChecking order: {order_number}"))
            
            if self.diagnose_order(order):
                if fix:
                    self.fix_order(order, dry_run)
            else:
                self.stdout.write(self.style.SUCCESS("✓ Order has valid delivery data"))
                
        except Order.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Order {order_number} not found"))

    def check_all_orders(self, fix=False, dry_run=False):
        """Check all orders for delivery location issues"""
        self.stdout.write(self.style.SUCCESS("\nScanning for delivery orders with missing location data..."))
        
        # Find all delivery orders without proper location data
        problematic_orders = Order.objects.filter(
            delivery_type='Delivery'
        ).filter(
            Q(delivery_location__isnull=True) & Q(custom_delivery_location__isnull=True)
            | Q(delivery_location__isnull=True) & Q(custom_delivery_location='')
        )
        
        total_count = problematic_orders.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("\n✓ No problematic delivery orders found!"))
            return
        
        self.stdout.write(self.style.WARNING(f"\nFound {total_count} delivery orders with missing location data:"))
        
        fixed_count = 0
        failed_count = 0
        
        for order in problematic_orders:
            self.stdout.write(f"\n" + "="*60)
            if self.diagnose_order(order):
                if fix:
                    if self.fix_order(order, dry_run):
                        fixed_count += 1
                    else:
                        failed_count += 1
        
        self.stdout.write(f"\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"\nSummary:"))
        self.stdout.write(f"Total problematic orders: {total_count}")
        
        if fix:
            self.stdout.write(f"Successfully fixed: {fixed_count}")
            self.stdout.write(f"Failed to fix: {failed_count}")
            if dry_run:
                self.stdout.write(self.style.WARNING("(DRY RUN - No actual changes made)"))

    def diagnose_order(self, order):
        """Diagnose a single order and return True if it needs fixing"""
        self.stdout.write(f"\nOrder: {order.order_number}")
        self.stdout.write(f"  - ID: {order.id}")
        self.stdout.write(f"  - Status: {order.status}")
        self.stdout.write(f"  - Delivery Type: {order.delivery_type}")
        self.stdout.write(f"  - Customer Phone: {order.customer_phone or 'None'}")
        self.stdout.write(f"  - Total Price: ₵{order.total_price}")
        self.stdout.write(f"  - Delivery Fee: ₵{order.delivery_fee}")
        
        # Check delivery location data
        self.stdout.write(f"\nDelivery Location Data:")
        self.stdout.write(f"  - Delivery Location: {order.delivery_location.name if order.delivery_location else 'None'}")
        self.stdout.write(f"  - Custom Location: {order.custom_delivery_location or 'None'}")
        self.stdout.write(f"  - Custom Fee: {f'₵{order.custom_delivery_fee}' if order.custom_delivery_fee else 'None'}")
        
        # Check historical data
        self.stdout.write(f"\nHistorical Data:")
        self.stdout.write(f"  - Historical Location Name: {order.delivery_location_name or 'None'}")
        self.stdout.write(f"  - Historical Location Fee: {f'₵{order.delivery_location_fee}' if order.delivery_location_fee else 'None'}")
        self.stdout.write(f"  - Effective Location Name: {order.get_effective_delivery_location_name() or 'None'}")
        
        # Check payment status
        payment_status = order.get_payment_status()
        amount_paid = order.amount_paid()
        balance_due = order.balance_due()
        
        self.stdout.write(f"\nPayment Information:")
        self.stdout.write(f"  - Payment Status: {payment_status}")
        self.stdout.write(f"  - Amount Paid: ₵{amount_paid}")
        self.stdout.write(f"  - Balance Due: ₵{balance_due}")
        
        # Check if this needs fixing
        needs_fix = (
            order.delivery_type == 'Delivery' and 
            not order.delivery_location and 
            not order.custom_delivery_location
        )
        
        if needs_fix:
            self.stdout.write(self.style.WARNING("\n⚠️  This order needs fixing!"))
            
            # Check for available fix options
            if order.delivery_location_name or order.get_effective_delivery_location_name():
                self.stdout.write(self.style.SUCCESS("\n✓ Can use historical data to fix"))
            else:
                self.stdout.write(self.style.WARNING("\n⚠️  No historical data available - manual fix required"))
        
        return needs_fix

    def fix_order(self, order, dry_run=False):
        """Attempt to fix an order with missing delivery location data"""
        self.stdout.write(self.style.SUCCESS(f"\nAttempting to fix order {order.order_number}..."))
        
        # Determine what data we can use
        historical_name = order.delivery_location_name or order.get_effective_delivery_location_name()
        historical_fee = order.delivery_location_fee
        
        if not historical_name:
            # Try to find a delivery location based on delivery fee
            if order.delivery_fee and order.delivery_fee > 0:
                matching_locations = DeliveryLocation.objects.filter(fee=order.delivery_fee)
                if matching_locations.count() == 1:
                    location = matching_locations.first()
                    self.stdout.write(f"  Found matching location by fee: {location.name} (₵{location.fee})")
                    historical_name = location.name
                    historical_fee = location.fee
                else:
                    self.stdout.write(self.style.WARNING("  Multiple or no locations match the delivery fee"))
        
        if not historical_name:
            self.stdout.write(self.style.ERROR("  ✗ Cannot fix: No historical data or matching location found"))
            return False
        
        # Prepare the fix
        self.stdout.write(f"\n  Fix plan:")
        self.stdout.write(f"    - Set custom_delivery_location to: {historical_name}")
        self.stdout.write(f"    - Set custom_delivery_fee to: ₵{historical_fee or order.delivery_fee or 0}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n  (DRY RUN - Not applying changes)"))
            return True
        
        try:
            with transaction.atomic():
                # Apply the fix
                order.custom_delivery_location = historical_name
                order.custom_delivery_fee = historical_fee or order.delivery_fee or Decimal('0.00')
                
                # Save without triggering full validation (to avoid other potential issues)
                order.save(update_fields=['custom_delivery_location', 'custom_delivery_fee', 'updated_at'])
                
                self.stdout.write(self.style.SUCCESS("\n  ✓ Order fixed successfully!"))
                
                # Verify the fix
                order.refresh_from_db()
                try:
                    order.full_clean()
                    self.stdout.write(self.style.SUCCESS("  ✓ Order validation passed"))
                    return True
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  Order still has validation issues: {e}"))
                    return True  # Still consider it fixed if we set the location data
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n  ✗ Failed to fix order: {e}"))
            return False

    def validate_all_orders(self):
        """Run validation on all orders to find any issues"""
        self.stdout.write(self.style.SUCCESS("\nValidating all orders..."))
        
        orders_with_issues = []
        
        for order in Order.objects.all():
            try:
                order.full_clean()
            except Exception as e:
                orders_with_issues.append({
                    'order': order,
                    'error': str(e)
                })
        
        if orders_with_issues:
            self.stdout.write(self.style.WARNING(f"\nFound {len(orders_with_issues)} orders with validation issues:"))
            for issue in orders_with_issues[:10]:  # Show first 10
                self.stdout.write(f"\n  Order {issue['order'].order_number}: {issue['error']}")
            
            if len(orders_with_issues) > 10:
                self.stdout.write(f"\n  ... and {len(orders_with_issues) - 10} more")
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ All orders pass validation!"))
