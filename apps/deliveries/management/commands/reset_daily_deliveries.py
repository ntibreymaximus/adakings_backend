from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.deliveries.models import DeliveryRider, DailyDeliveryStats


class Command(BaseCommand):
    help = 'Reset daily deliveries and store them in DailyDeliveryStats'

    def handle(self, *args, **options):
        today = timezone.now().date()
        for rider in DeliveryRider.objects.all():
            # Save today's delivery count
            DailyDeliveryStats.objects.update_or_create(
                rider=rider,
                date=today,
                defaults={'deliveries_count': rider.today_deliveries}
            )

            # Reset today's deliveries
            rider.today_deliveries = 0
            rider.save(update_fields=['today_deliveries'])

        self.stdout.write(self.style.SUCCESS('Successfully reset and recorded daily deliveries for all riders'))
