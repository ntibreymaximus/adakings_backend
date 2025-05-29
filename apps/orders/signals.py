from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem, Order

@receiver(post_save, sender=OrderItem)
def update_order_total_on_item_save(sender, instance, **kwargs):
    """
    Recalculate and save the order's total price when an OrderItem is saved.
    """
    order = instance.order
    order.calculate_total()  # This updates order.total_price in memory
    # Save only the total_price and updated_at to avoid triggering full save logic unnecessarily
    # and to prevent recursion if the Order.save() method itself triggers signals.
    order.save(update_fields=['total_price', 'updated_at'])

@receiver(post_delete, sender=OrderItem)
def update_order_total_on_item_delete(sender, instance, **kwargs):
    """
    Recalculate and save the order's total price when an OrderItem is deleted.
    """
    order = instance.order
    order.calculate_total()  # This updates order.total_price in memory
    # Save only the total_price and updated_at
    order.save(update_fields=['total_price', 'updated_at'])

