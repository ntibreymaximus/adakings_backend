# Generated migration to remove commission, delivery fee, proof of delivery, and extra timestamps

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deliveries', '0005_copy_delivery_locations_data'),
    ]

    operations = [
        # First, remove indexes that depend on fields we're removing
        migrations.RemoveIndex(
            model_name='orderassignment',
            name='deliveries__status_1c5daf_idx',
        ),
        migrations.RemoveIndex(
            model_name='orderassignment',
            name='deliveries__rider_i_4847be_idx',
        ),
        
        # Remove commission and fee fields
        migrations.RemoveField(
            model_name='orderassignment',
            name='delivery_fee',
        ),
        migrations.RemoveField(
            model_name='orderassignment',
            name='rider_commission',
        ),
        
        # Remove proof of delivery fields
        migrations.RemoveField(
            model_name='orderassignment',
            name='customer_signature',
        ),
        migrations.RemoveField(
            model_name='orderassignment',
            name='distance_km',
        ),
        
        # Remove unnecessary timestamps (keeping picked_up_at and delivered_at)
        migrations.RemoveField(
            model_name='orderassignment',
            name='assigned_at',
        ),
        migrations.RemoveField(
            model_name='orderassignment',
            name='accepted_at',
        ),
        migrations.RemoveField(
            model_name='orderassignment',
            name='returned_at',
        ),
        migrations.RemoveField(
            model_name='orderassignment',
            name='cancelled_at',
        ),
        
        # Add back the indexes without the removed fields
        migrations.AddIndex(
            model_name='orderassignment',
            index=models.Index(fields=['status'], name='deliveries__status_idx'),
        ),
        migrations.AddIndex(
            model_name='orderassignment',
            index=models.Index(fields=['rider', 'status'], name='deliveries__rider_status_idx'),
        ),
    ]
