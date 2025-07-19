from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone
from apps.deliveries.models import DeliveryRider, OrderAssignment


class Command(BaseCommand):
    help = 'Fix rider delivery statistics by recalculating from OrderAssignment records'

    def handle(self, *args, **options):
        self.stdout.write('Fixing rider delivery statistics...')
        
        # Get all riders
        riders = DeliveryRider.objects.all()
        
        today = timezone.now().date()
        
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
            
            # Count today's deliveries
            today_count = OrderAssignment.objects.filter(
                rider=rider,
                status__in=['delivered', 'returned'],
                delivered_at__date=today
            ).count()
            
            # Update rider stats
            rider.total_deliveries = delivered_count
            rider.current_orders = current_count
            rider.today_deliveries = today_count
            rider.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated {rider.name}: '
                    f'total_deliveries={delivered_count}, '
                    f'current_orders={current_count}, '
                    f'today_deliveries={today_count}'
                )
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully fixed rider statistics'))
