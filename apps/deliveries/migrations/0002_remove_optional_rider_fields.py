# Generated migration to remove optional fields from DeliveryRider model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deliveries', '0001_remove_photo_proof'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deliveryrider',
            name='email',
        ),
        migrations.RemoveField(
            model_name='deliveryrider',
            name='vehicle_type',
        ),
        migrations.RemoveField(
            model_name='deliveryrider',
            name='vehicle_number',
        ),
        migrations.RemoveField(
            model_name='deliveryrider',
            name='license_number',
        ),
        migrations.RemoveField(
            model_name='deliveryrider',
            name='address',
        ),
        migrations.RemoveField(
            model_name='deliveryrider',
            name='emergency_contact',
        ),
    ]
