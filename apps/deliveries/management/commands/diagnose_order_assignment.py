from django.core.management.base import BaseCommand
from django.db import connection
from apps.orders.models import Order
from apps.deliveries.models import OrderAssignment, DeliveryRider
import json


class Command(BaseCommand):
    help = 'Diagnose order assignment issues'

    def add_arguments(self, parser):
        parser.add_argument(
            'order_id',
            type=str,
            help='Order ID or order number to diagnose'
        )

    def handle(self, *args, **options):
        order_id = options['order_id']
        
        # Find the order
        try:
            if order_id.isdigit():
                order = Order.objects.get(id=int(order_id))
            else:
                order = Order.objects.get(order_number=order_id)
        except Order.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Order not found: {order_id}'))
            return

        self.stdout.write(self.style.SUCCESS(f'\nOrder found: {order.order_number} (ID: {order.id})'))
        
        # Display order details
        self.stdout.write(f'Status: {order.status}')
        self.stdout.write(f'Delivery Type: {order.delivery_type}')
        self.stdout.write(f'Delivery Location: {order.delivery_location.name if order.delivery_location else "None"}')
        self.stdout.write(f'Customer Phone: {order.customer_phone or "None"}')
        self.stdout.write(f'Total Price: ₵{order.total_price}')
        self.stdout.write(f'Created: {order.created_at}')
        self.stdout.write(f'Updated: {order.updated_at}')
        
        # Check payment status
        payment_status = order.get_payment_status()
        self.stdout.write(f'Payment Status: {payment_status}')
        
        # Check for existing assignment
        try:
            assignment = order.delivery_assignment
            self.stdout.write(self.style.WARNING(f'\nExisting assignment found:'))
            self.stdout.write(f'Assignment ID: {assignment.id}')
            self.stdout.write(f'Rider: {assignment.rider.name if assignment.rider else "None"}')
            self.stdout.write(f'Status: {assignment.status}')
            self.stdout.write(f'Picked up at: {assignment.picked_up_at or "Not picked up"}')
            self.stdout.write(f'Delivered at: {assignment.delivered_at or "Not delivered"}')
        except OrderAssignment.DoesNotExist:
            self.stdout.write(self.style.SUCCESS('\nNo existing assignment found'))
        
        # Check for any assignments in the database
        all_assignments = OrderAssignment.objects.filter(order=order)
        if all_assignments.exists():
            self.stdout.write(self.style.WARNING(f'\nFound {all_assignments.count()} assignment(s) in database:'))
            for a in all_assignments:
                self.stdout.write(f'  - ID: {a.id}, Rider: {a.rider.name if a.rider else "None"}, Status: {a.status}')
        
        # Check available riders
        self.stdout.write(self.style.SUCCESS('\nAvailable riders:'))
        from django.db.models import F
        available_riders = DeliveryRider.objects.filter(
            status='active',
            is_available=True,
            current_orders__lt=F('max_concurrent_orders')
        )
        
        if available_riders.exists():
            for rider in available_riders[:5]:  # Show top 5
                self.stdout.write(f'  - {rider.name}: {rider.current_orders}/{rider.max_concurrent_orders} orders')
        else:
            self.stdout.write(self.style.WARNING('  No available riders found'))
        
        # Check database constraints
        self.stdout.write(self.style.SUCCESS('\nDatabase constraints check:'))
        with connection.cursor() as cursor:
            # Check for unique constraint on order assignment
            cursor.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type='index' AND tbl_name='deliveries_orderassignment'
                AND sql LIKE '%UNIQUE%';
            """)
            constraints = cursor.fetchall()
            if constraints:
                for name, sql in constraints:
                    self.stdout.write(f'  - {name}: {sql}')
            else:
                self.stdout.write('  No unique constraints found on deliveries_orderassignment')
        
        # Check Order status constants
        self.stdout.write(self.style.SUCCESS('\nOrder status constants:'))
        self.stdout.write(f'  STATUS_PENDING: {Order.STATUS_PENDING}')
        self.stdout.write(f'  STATUS_ACCEPTED: {Order.STATUS_ACCEPTED}')
        self.stdout.write(f'  STATUS_READY: {Order.STATUS_READY}')
        self.stdout.write(f'  STATUS_OUT_FOR_DELIVERY: {Order.STATUS_OUT_FOR_DELIVERY}')
        self.stdout.write(f'  STATUS_FULFILLED: {Order.STATUS_FULFILLED}')
        self.stdout.write(f'  STATUS_CANCELLED: {Order.STATUS_CANCELLED}')
        
        # Check valid statuses for assignment
        valid_statuses = [Order.STATUS_ACCEPTED, Order.STATUS_OUT_FOR_DELIVERY]
        is_valid_for_assignment = order.status in valid_statuses
        self.stdout.write(f'\nOrder status "{order.status}" is {"" if is_valid_for_assignment else "NOT "}valid for assignment')
        self.stdout.write(f'Valid statuses: {valid_statuses}')
