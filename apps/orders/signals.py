from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem, Order
import logging

logger = logging.getLogger(__name__)

# Flag to prevent signal recursion
_signal_processing = set()

@receiver(post_save, sender=OrderItem)
def update_order_total_on_item_save(sender, instance, **kwargs):
    """
    Recalculate and save the order's total price when an OrderItem is saved.
    Also broadcast the update via WebSocket.
    """
    # Use unique identifier to prevent recursion
    signal_key = f"orderitem_save_{instance.id}_{instance.order.id}"
    
    if signal_key in _signal_processing:
        return  # Prevent recursion
    
    try:
        _signal_processing.add(signal_key)
        
        order = instance.order
        order.calculate_total()  # This updates order.total_price in memory
        
        # Save only the total_price and updated_at to avoid triggering full save logic
        # Use update_fields to prevent triggering the Order post_save signal
        order.save(update_fields=['total_price', 'updated_at'])
        
        # Broadcast order update via WebSocket
        try:
            from .consumers import broadcast_order_updated
            broadcast_order_updated(order)
        except ImportError:
            # Gracefully handle if consumers module is not available
            pass
        except Exception as e:
            logger.error(f"Error broadcasting order item change: {e}")
            
    finally:
        _signal_processing.discard(signal_key)

@receiver(post_delete, sender=OrderItem)
def update_order_total_on_item_delete(sender, instance, **kwargs):
    """
    Recalculate and save the order's total price when an OrderItem is deleted.
    Also broadcast the update via WebSocket.
    """
    # Use unique identifier to prevent recursion
    signal_key = f"orderitem_delete_{instance.order.id}"
    
    if signal_key in _signal_processing:
        return  # Prevent recursion
    
    try:
        _signal_processing.add(signal_key)
        
        order = instance.order
        order.calculate_total()  # This updates order.total_price in memory
        
        # Save only the total_price and updated_at to avoid triggering full save logic
        order.save(update_fields=['total_price', 'updated_at'])
        
        # Broadcast order update via WebSocket
        try:
            from .consumers import broadcast_order_updated
            broadcast_order_updated(order)
        except ImportError:
            # Gracefully handle if consumers module is not available
            pass
        except Exception as e:
            logger.error(f"Error broadcasting order item deletion: {e}")
            
    finally:
        _signal_processing.discard(signal_key)

