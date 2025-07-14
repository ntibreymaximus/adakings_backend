from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver
from .models import OrderItem, Order
from apps.deliveries.models import DeliveryLocation
import logging

logger = logging.getLogger(__name__)

# Flag to prevent signal recursion
_signal_processing = set()

@receiver(post_save, sender=OrderItem)
def update_order_total_on_item_save(sender, instance, **kwargs):
    """
    Recalculate and save the order's total price when an OrderItem is saved.
    """
    # Use unique identifier to prevent recursion
    signal_key = f"orderitem_save_{instance.id}_{instance.order.id}"
    
    if signal_key in _signal_processing:
        return  # Prevent recursion
    
    try:
        _signal_processing.add(signal_key)
        
        order = instance.order
        logger.debug(f"Signal: Recalculating total for order: {order.id} after item save")
        order.calculate_total()  # This updates order.total_price in memory
        
        # Save only the total_price and updated_at to avoid triggering full save logic
        # Use update_fields to prevent triggering the Order post_save signal
        order.save(update_fields=['total_price', 'updated_at'])
        logger.debug(f"Signal: Updated total for order: {order.id} is {order.total_price}")
        
            
    finally:
        _signal_processing.discard(signal_key)

@receiver(post_delete, sender=OrderItem)
def update_order_total_on_item_delete(sender, instance, **kwargs):
    """
    Recalculate and save the order's total price when an OrderItem is deleted.
    """
    # Use unique identifier to prevent recursion
    signal_key = f"orderitem_delete_{instance.order.id}"
    
    if signal_key in _signal_processing:
        return  # Prevent recursion
    
    try:
        _signal_processing.add(signal_key)
        
        order = instance.order
        logger.debug(f"Recalculating total for order: {order.id}")
        order.calculate_total()  # This updates order.total_price in memory
        
        # Save only the total_price and updated_at to avoid triggering full save logic
        order.save(update_fields=['total_price', 'updated_at'])
        logger.debug(f"Updated total for order: {order.id} is {order.total_price}")
        
            
    finally:
        _signal_processing.discard(signal_key)


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """
    Track when order status is about to change to detect Fulfilled status.
    Also preserve delivery location history when needed.
    """
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            
            # Preserve delivery history if delivery location is being changed or removed
            if old_instance.delivery_location != instance.delivery_location:
                # If we had a delivery location and don't have historical data yet
                if old_instance.delivery_location and not instance.delivery_location_name:
                    instance.delivery_location_name = old_instance.delivery_location.name
                    instance.delivery_location_fee = old_instance.delivery_location.fee
                    logger.info(f"Preserved delivery history for order {instance.order_number} before location change")
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def update_delivery_assignment_on_fulfilled(sender, instance, created, **kwargs):
    """
    Automatically update delivery assignment status to 'delivered' when order status becomes 'Fulfilled'.
    """
    # Skip for new orders
    if created:
        return
    
    # Check if this update is coming from the delivery assignment signal to prevent recursion
    if getattr(instance, '_updating_from_delivery', False):
        return
    
    # Check if status changed to Fulfilled
    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status
    
    if old_status != new_status and new_status == Order.STATUS_FULFILLED:
        # Import here to avoid circular imports
        from apps.deliveries.models import OrderAssignment
        
        try:
            # Get the delivery assignment for this order
            assignment = instance.delivery_assignment
            
            # Update to 'delivered' if assignment is in any active state (not already delivered, returned, or cancelled)
            active_statuses = ['assigned', 'accepted', 'picked_up', 'in_transit']
            if assignment and assignment.status in active_statuses:
                logger.info(f"Order {instance.order_number} fulfilled - updating delivery assignment from '{assignment.status}' to 'delivered'")
                assignment.status = 'delivered'
                assignment.save()
                logger.info(f"Delivery assignment for order {instance.order_number} marked as delivered")
            elif assignment and assignment.status in ['delivered', 'returned', 'cancelled']:
                logger.info(f"Order {instance.order_number} fulfilled but delivery assignment status is already '{assignment.status}'")
            elif assignment:
                logger.warning(f"Order {instance.order_number} fulfilled but delivery assignment has unexpected status '{assignment.status}'")
        except OrderAssignment.DoesNotExist:
            # No delivery assignment exists for this order (might be a pickup order)
            logger.debug(f"No delivery assignment found for order {instance.order_number}")


@receiver(pre_delete, sender=DeliveryLocation)
def preserve_order_history_before_location_delete(sender, instance, **kwargs):
    """
    Before deleting a delivery location, ensure all orders have historical data.
    """
    # Find all orders using this delivery location that don't have historical data
    orders_to_update = Order.objects.filter(
        delivery_location=instance,
        delivery_location_name__isnull=True
    )
    
    count = orders_to_update.count()
    if count > 0:
        logger.info(f"Preserving historical data for {count} orders before deleting location '{instance.name}'")
        
        for order in orders_to_update:
            order.delivery_location_name = instance.name
            order.delivery_location_fee = instance.fee
            order.save(update_fields=['delivery_location_name', 'delivery_location_fee'])

