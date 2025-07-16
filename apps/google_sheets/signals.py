import logging
from typing import Dict, Any

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from .google_client_shared import get_google_sheets_client_shared as get_google_sheets_client
from .middleware import get_current_user

logger = logging.getLogger(__name__)


def prepare_order_data(order: Order) -> Dict[str, Any]:
    """
    Prepare order data for Google Sheets.
    
    Args:
        order: The Order instance
        
    Returns:
        Dictionary with formatted order data
    """
    # Format items
    items_list = []
    for item in order.items.all():
        item_str = f"{item.quantity}x {item.menu_item.name}"
        if item.unit_price != item.menu_item.price:
            item_str += f" @ {item.unit_price}"
        if item.notes:
            item_str += f" ({item.notes})"
        items_list.append(item_str)
    items_str = "; ".join(items_list)
    
    # Calculate subtotal (total - delivery fee)
    subtotal = order.total_price - order.delivery_fee
    
    # Get delivery location name
    delivery_location = ""
    if order.delivery_location:
        delivery_location = order.delivery_location.name
    elif order.custom_delivery_location:
        delivery_location = order.custom_delivery_location
    
    # Get created by user from middleware or order attribute
    created_by = ""
    current_user = get_current_user()
    if current_user and current_user.is_authenticated:
        created_by = current_user.get_full_name() or current_user.username
    elif hasattr(order, '_current_user') and order._current_user:
        created_by = order._current_user.get_full_name() or order._current_user.username
    
    return {
        'order_number': order.order_number,
        'time': order.created_at.strftime('%H:%M:%S'),
        'customer_phone': order.customer_phone or '',
        'delivery_type': order.delivery_type,
        'delivery_location': delivery_location,
        'items': items_str,
        'subtotal': float(subtotal),
        'delivery_fee': float(order.delivery_fee),
        'total_price': float(order.total_price),
        'payment_status': order.get_payment_status(),
        'order_status': order.status,
        'notes': order.notes,
        'created_by': created_by,
    }


@receiver(post_save, sender=Order)
def sync_order_to_sheets(sender, instance, created, **kwargs):
    """
    Sync order to Google Sheets when created or updated.
    """
    # Skip if Google Sheets sync is disabled
    if not getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', True):
        return
    
    # Skip if this is a signal during import to avoid circular updates
    if getattr(instance, '_skip_sheets_sync', False):
        return
    
    try:
        client = get_google_sheets_client()
        order_data = prepare_order_data(instance)
        
        if created:
            # Add new order to sheet
            success = client.add_order_to_sheet(order_data)
            if success:
                logger.info(f"Order {instance.order_number} synced to Google Sheets")
            else:
                logger.error(f"Failed to sync order {instance.order_number} to Google Sheets")
        else:
            # Update existing order in sheet
            updates = {
                'customer_phone': order_data['customer_phone'],
                'delivery_type': order_data['delivery_type'],
                'delivery_location': order_data['delivery_location'],
                'items': order_data['items'],
                'subtotal': order_data['subtotal'],
                'delivery_fee': order_data['delivery_fee'],
                'total_price': order_data['total_price'],
                'payment_status': order_data['payment_status'],
                'order_status': order_data['order_status'],
                'notes': order_data['notes'],
            }
            success = client.update_order_in_sheet(instance.order_number, updates)
            if success:
                logger.info(f"Order {instance.order_number} updated in Google Sheets")
            else:
                logger.error(f"Failed to update order {instance.order_number} in Google Sheets")
                
    except Exception as e:
        logger.error(f"Error syncing order to Google Sheets: {e}")


@receiver(post_save, sender=OrderItem)
def sync_order_items_to_sheets(sender, instance, **kwargs):
    """
    Update order in Google Sheets when items are modified.
    """
    # Skip if Google Sheets sync is disabled
    if not getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', True):
        return
    
    try:
        order = instance.order
        
        # Skip if order has skip flag
        if getattr(order, '_skip_sheets_sync', False):
            return
        
        client = get_google_sheets_client()
        order_data = prepare_order_data(order)
        
        updates = {
            'items': order_data['items'],
            'subtotal': order_data['subtotal'],
            'total_price': order_data['total_price'],
        }
        
        success = client.update_order_in_sheet(order.order_number, updates)
        if success:
            logger.info(f"Order {order.order_number} items updated in Google Sheets")
            
    except Exception as e:
        logger.error(f"Error syncing order items to Google Sheets: {e}")


@receiver(post_save, sender=Payment)
def sync_payment_to_sheets(sender, instance, **kwargs):
    """
    Update order payment status in Google Sheets when payment is made.
    """
    # Skip if Google Sheets sync is disabled
    if not getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', True):
        return
    
    try:
        order = instance.order
        
        # Skip if order has skip flag
        if getattr(order, '_skip_sheets_sync', False):
            return
        
        client = get_google_sheets_client()
        
        updates = {
            'payment_status': order.get_payment_status(),
        }
        
        success = client.update_order_in_sheet(order.order_number, updates)
        if success:
            logger.info(f"Order {order.order_number} payment status updated in Google Sheets")
            
    except Exception as e:
        logger.error(f"Error syncing payment to Google Sheets: {e}")


@receiver(post_delete, sender=Payment)
def sync_payment_delete_to_sheets(sender, instance, **kwargs):
    """
    Update order payment status in Google Sheets when payment is deleted.
    """
    # Skip if Google Sheets sync is disabled
    if not getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', True):
        return
    
    try:
        order = instance.order
        
        # Skip if order has skip flag
        if getattr(order, '_skip_sheets_sync', False):
            return
        
        client = get_google_sheets_client()
        
        updates = {
            'payment_status': order.get_payment_status(),
        }
        
        success = client.update_order_in_sheet(order.order_number, updates)
        if success:
            logger.info(f"Order {order.order_number} payment status updated in Google Sheets after payment deletion")
            
    except Exception as e:
        logger.error(f"Error syncing payment deletion to Google Sheets: {e}")
