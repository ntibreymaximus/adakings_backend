from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.audit.utils import log_refund
import uuid


class Command(BaseCommand):
    help = 'Process automatic refunds for overpaid orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be refunded without actually processing refunds',
        )
        parser.add_argument(
            '--order-number',
            type=str,
            help='Process refund for a specific order number',
        )
        parser.add_argument(
            '--min-amount',
            type=float,
            default=0.01,
            help='Minimum refund amount to process (default: 0.01)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        order_number = options['order_number']
        min_amount = Decimal(str(options['min_amount']))

        self.stdout.write(self.style.SUCCESS('Processing automatic refunds for overpaid orders...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual refunds will be processed'))

        # Get orders to process
        if order_number:
            try:
                orders = Order.objects.filter(order_number=order_number)
                if not orders.exists():
                    self.stdout.write(self.style.ERROR(f'Order {order_number} not found'))
                    return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error finding order {order_number}: {str(e)}'))
                return
        else:
            # Get all orders that might need refunds
            orders = Order.objects.all()

        refunds_processed = 0
        total_refund_amount = Decimal('0.00')
        
        for order in orders:
            try:
                # Calculate refund amount due
                refund_due = order.refund_amount()
                
                if refund_due >= min_amount:
                    self.stdout.write(f'\nOrder {order.order_number}:')
                    self.stdout.write(f'  Total Price: ₵{order.total_price}')
                    self.stdout.write(f'  Amount Paid: ₵{order.amount_paid()}')
                    self.stdout.write(f'  Amount Overpaid: ₵{order.amount_overpaid()}')
                    self.stdout.write(f'  Refund Due: ₵{refund_due}')
                    
                    if not dry_run:
                        # Process the refund
                        with transaction.atomic():
                            payment_reference = uuid.uuid4()
                            
                            # Create refund payment record
                            refund_payment = Payment.objects.create(
                                order=order,
                                amount=refund_due,
                                payment_method=Payment.PAYMENT_METHOD_CASH,  # Default to cash refund
                                payment_type=Payment.PAYMENT_TYPE_REFUND,
                                status=Payment.STATUS_COMPLETED,
                                reference=payment_reference,
                                notes=f"Automatic refund for overpayment of ₵{refund_due} (System processed)"
                            )
                            
                            # Log the refund
                            log_refund(
                                user=None,  # System processed
                                payment_obj=refund_payment,
                                amount=refund_due,
                                reason=f"Automatic refund for overpayment on order {order.order_number}"
                            )
                            
                            refunds_processed += 1
                            total_refund_amount += refund_due
                            
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Refund processed: ₵{refund_due}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  → Would process refund: ₵{refund_due}'))
                        refunds_processed += 1
                        total_refund_amount += refund_due
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing order {order.order_number}: {str(e)}'))

        # Summary
        self.stdout.write(f'\n{"-" * 50}')
        self.stdout.write(f'Summary:')
        self.stdout.write(f'  Orders processed: {refunds_processed}')
        self.stdout.write(f'  Total refund amount: ₵{total_refund_amount}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('  No actual refunds were processed (dry run mode)'))
        else:
            self.stdout.write(self.style.SUCCESS('  All refunds have been processed successfully'))
