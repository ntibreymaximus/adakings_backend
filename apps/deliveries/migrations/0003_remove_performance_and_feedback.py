# Generated migration to remove RiderPerformance and DeliveryFeedback models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deliveries', '0002_remove_optional_rider_fields'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DeliveryFeedback',
        ),
        migrations.DeleteModel(
            name='RiderPerformance',
        ),
    ]
