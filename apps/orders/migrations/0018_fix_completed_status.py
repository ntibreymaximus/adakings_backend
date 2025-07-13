# Generated manually on 2025-07-12
from django.db import migrations

def fix_completed_status(apps, schema_editor):
    """Fix orders with invalid 'Completed' status by changing them to 'Fulfilled'"""
    Order = apps.get_model('orders', 'Order')
    
    # Update any orders with 'Completed' status to 'Fulfilled'
    updated_count = Order.objects.filter(status='Completed').update(status='Fulfilled')
    
    if updated_count > 0:
        print(f"Updated {updated_count} orders from 'Completed' to 'Fulfilled' status")

def reverse_fix(apps, schema_editor):
    """Reverse operation - not applicable as we're fixing invalid data"""
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0017_alter_order_delivery_location_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_completed_status, reverse_fix),
    ]
