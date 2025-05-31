from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.orders.models import Order
from django.db import transaction

class Command(BaseCommand):
    help = 'Corrects blank or improperly formatted order_number fields for existing orders.'

    def handle(self, *args, **options):
        updated_count = 0
        try:
            correct_format_regex = r'^\d{6}-\d{3}$'
            # Find orders that are:
            # (a) blank or null OR
            # (b) not blank, not null, AND do not match the regex
            orders_to_update = Order.objects.filter(
                Q(order_number__isnull=True) | Q(order_number='') |
                (
                    Q(order_number__isnull=False) &
                    ~Q(order_number='') &
                    ~Q(order_number__regex=correct_format_regex)
                )
            ).distinct()

            if not orders_to_update.exists():
                self.stdout.write(self.style.NOTICE('No orders found with blank or incorrectly formatted order_number.'))
                return

            with transaction.atomic(): # Use a transaction for atomicity
                for order in orders_to_update:
                    original_order_id = order.id # Keep id for logging before save
                    try:
                        # Set order_number to None to ensure the model's save() method
                        # triggers generate_order_number()
                        order.order_number = None
                        order.save()
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'Successfully updated order_number for order ID {original_order_id} to {order.order_number}'
                        ))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(
                            f'Failed to update order ID {original_order_id}: {e}'
                        ))
            
            if updated_count > 0:
                self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} orders.'))
            else:
                # This case might be reached if all attempts within the loop failed
                self.stdout.write(self.style.NOTICE('No orders were updated. Check error messages if any.'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An unexpected error occurred: {e}'))

