# Generated manually
from django.db import migrations, models
from decimal import Decimal


def populate_denormalized_fields(apps, schema_editor):
    """Populate the new denormalized fields from existing menu items"""
    OrderItem = apps.get_model('orders', 'OrderItem')
    
    for order_item in OrderItem.objects.select_related('menu_item').all():
        if order_item.menu_item:
            order_item.item_name = order_item.menu_item.name
            order_item.item_type = order_item.menu_item.item_type
            order_item.save(update_fields=['item_name', 'item_type'])


def reverse_populate(apps, schema_editor):
    """Clear the denormalized fields"""
    OrderItem = apps.get_model('orders', 'OrderItem')
    OrderItem.objects.update(item_name='', item_type='')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0018_fix_completed_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='item_name',
            field=models.CharField(max_length=200, blank=True, help_text='Stored item name for historical reference'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='item_type',
            field=models.CharField(max_length=10, blank=True, help_text='Stored item type for historical reference'),
        ),
        migrations.RunPython(populate_denormalized_fields, reverse_populate),
    ]
