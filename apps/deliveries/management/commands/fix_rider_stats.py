from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.deliveries.models import DeliveryRider, OrderAssignment


class Command(BaseCommand):
    help = 'Fix rider delivery statistics by recalculating from OrderAssignment records'

    def handle(self, *args, **options):
        self.stdout.write('Fixing rider delivery statistics...')
        
        # Get all riders
        riders = DeliveryRider.objects.all()
        
        for rider in riders:
            # Count delivered orders for this rider
            delivered_count = OrderAssignment.objects.filter(
                rider=rider,
                status__in=['delivered', 'returned']
            ).count()
            
            # Count current active orders
            current_count = OrderAssignment.objects.filter(
                rider=rider,
                status__in=['assigned', 'accepted', 'picked_up', 'in_transit']
            ).count()
            
            # Update rider stats
            rider.total_deliveries = delivered_count
            rider.current_orders = current_count
            rider.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated {rider.name}: '
                    f'total_deliveries={delivered_count}, '
                    f'current_orders={current_count}'
                )
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully fixed rider statistics'))
