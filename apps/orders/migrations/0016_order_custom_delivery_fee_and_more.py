# Generated by Django 5.2.2 on 2025-07-05 15:44

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0015_order_orders_orde_created_f0ce29_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='custom_delivery_fee',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Custom delivery fee (used when delivery_location is not set)', max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))]),
        ),
        migrations.AddField(
            model_name='order',
            name='custom_delivery_location',
            field=models.CharField(blank=True, help_text='Custom delivery location name (used when delivery_location is not set)', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_location',
            field=models.ForeignKey(blank=True, help_text='Select delivery location (Required for delivery orders unless custom location is provided).', null=True, on_delete=django.db.models.deletion.SET_NULL, to='orders.deliverylocation'),
        ),
    ]
