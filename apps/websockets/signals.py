from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Get channel layer
channel_layer = get_channel_layer()

# Track previous states for change detection
_previous_states = {}

def send_websocket_notification(group_name, event_type, payload):
    """Send notification to WebSocket group."""
    try:
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': event_type,
                    'payload': payload
                }
            )
    except RuntimeError as e:
        # Handle "cannot schedule new futures after interpreter shutdown"
        if "cannot schedule new futures after interpreter shutdown" in str(e):
            logger.debug(f"WebSocket notification skipped during shutdown: {group_name}")
        else:
            raise
    except Exception as e:
        logger.error(f"Error sending WebSocket notification to {group_name}: {e}")

def get_model_changes(old_data: Dict, new_data: Dict) -> Dict[str, Dict]:
    """Compare two dictionaries and return changes."""
    changes = {}
    all_keys = set(old_data.keys()) | set(new_data.keys())
    
    for key in all_keys:
        old_value = old_data.get(key)
        new_value = new_data.get(key)
        
        if old_value != new_value:
            changes[key] = {
                'old': old_value,
                'new': new_value
            }
    
    return changes

def send_autoreload_notification(event_type: str, model_name: str, instance_data: Dict, changes: Optional[Dict] = None):
    """Send autoreload notification to all connected clients."""
    payload = {
        'event': 'autoreload',
        'type': event_type,
        'model': model_name,
        'data': instance_data,
        'changes': changes or {},
        'timestamp': timezone.now().isoformat()
    }
    
    # Send to general autoreload channel
    send_websocket_notification('autoreload', 'autoreload_update', payload)
    
    # Send to specific model channels
    model_channel = f'{model_name.lower()}_autoreload'
    send_websocket_notification(model_channel, 'autoreload_update', payload)

# Order-related signals
@receiver(pre_save, sender='orders.Order')
def track_order_changes(sender, instance, **kwargs):
    """Track order changes before save."""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_order_data = {
                'status': old_instance.status,
                'total_price': str(old_instance.total_price),
                'customer_phone': old_instance.customer_phone,
                'delivery_type': old_instance.delivery_type,
            }
        except sender.DoesNotExist:
            instance._old_order_data = None
    else:
        instance._old_order_data = None

@receiver(post_save, sender='orders.Order')
def order_created_or_updated(sender, instance, created, **kwargs):
    """Send order update notification via WebSocket."""
    try:
        event_type = 'order_created' if created else 'order_updated'
        
        # Get current order data
        current_data = {
            'id': instance.id,
            'order_number': instance.order_number,
            'status': instance.status,
            'total_amount': str(instance.total_price),
            'customer_phone': instance.customer_phone,
            'delivery_type': instance.delivery_type,
            'created_at': instance.created_at.isoformat(),
            'updated_at': instance.updated_at.isoformat(),
        }
        
        payload = {
            'event': event_type,
            'order': current_data
        }
        
        # Send to orders group
        send_websocket_notification('orders_updates', 'order_update', payload)
        
        # Send to user-specific group if user exists
        if hasattr(instance, 'user') and instance.user:
            send_websocket_notification(
                f'user_{instance.user.id}', 
                'user_notification', 
                payload
            )
        
        # Send autoreload notification if not created
        if not created and hasattr(instance, '_old_order_data') and instance._old_order_data:
            changes = get_model_changes(instance._old_order_data, {
                'status': instance.status,
                'total_price': str(instance.total_price),
                'customer_phone': instance.customer_phone,
                'delivery_type': instance.delivery_type,
            })
            
            if changes:
                send_autoreload_notification('updated', 'Order', current_data, changes)
        elif created:
            send_autoreload_notification('created', 'Order', current_data)
            
        logger.info(f"Order {event_type} WebSocket notification sent: {instance.order_number}")
        
    except Exception as e:
        logger.error(f"Error sending order WebSocket notification: {e}")

@receiver(post_delete, sender='orders.Order')
def order_deleted(sender, instance, **kwargs):
    """Send order deletion notification via WebSocket."""
    try:
        payload = {
            'event': 'order_deleted',
            'order': {
                'id': instance.id,
                'order_number': instance.order_number,
            }
        }
        
        send_websocket_notification('orders_updates', 'order_update', payload)
        
        logger.info(f"Order deletion WebSocket notification sent: {instance.order_number}")
        
    except Exception as e:
        logger.error(f"Error sending order deletion WebSocket notification: {e}")

# Menu-related signals
@receiver(post_save, sender='menu.MenuItem')
def menu_item_created_or_updated(sender, instance, created, **kwargs):
    """Send menu item update notification via WebSocket."""
    try:
        event_type = 'menu_item_created' if created else 'menu_item_updated'
        
        payload = {
            'event': event_type,
            'menu_item': {
                'id': instance.id,
                'name': instance.name,
                'price': str(instance.price),
                'is_available': instance.is_available,
                'item_type': instance.item_type,
                'updated_at': instance.updated_at.isoformat(),
            }
        }
        
        send_websocket_notification('menu_updates', 'menu_update', payload)
        
        logger.info(f"Menu item {event_type} WebSocket notification sent: {instance.name}")
        
    except Exception as e:
        logger.error(f"Error sending menu WebSocket notification: {e}")

@receiver(post_delete, sender='menu.MenuItem')
def menu_item_deleted(sender, instance, **kwargs):
    """Send menu item deletion notification via WebSocket."""
    try:
        payload = {
            'event': 'menu_item_deleted',
            'menu_item': {
                'id': instance.id,
                'name': instance.name,
            }
        }
        
        send_websocket_notification('menu_updates', 'menu_update', payload)
        
        logger.info(f"Menu item deletion WebSocket notification sent: {instance.name}")
        
    except Exception as e:
        logger.error(f"Error sending menu deletion WebSocket notification: {e}")

# Payment/Transaction-related signals
@receiver(post_save, sender='payments.Payment')
def payment_created_or_updated(sender, instance, created, **kwargs):
    """Send payment update notification via WebSocket."""
    try:
        event_type = 'payment_created' if created else 'payment_updated'
        
        payload = {
            'event': event_type,
            'payment': {
                'id': instance.id,
                'order_id': instance.order.id if instance.order else None,
                'amount': str(instance.amount),
                'payment_method': instance.payment_method,
                'status': instance.status,
                'created_at': instance.created_at.isoformat(),
                'updated_at': instance.updated_at.isoformat(),
            }
        }
        
        send_websocket_notification('transaction_updates', 'transaction_update', payload)
        
        # Send to user-specific group if order has user
        if instance.order and hasattr(instance.order, 'user') and instance.order.user:
            send_websocket_notification(
                f'user_{instance.order.user.id}', 
                'user_notification', 
                payload
            )
            
        logger.info(f"Payment {event_type} WebSocket notification sent: {instance.id}")
        
    except Exception as e:
        logger.error(f"Error sending payment WebSocket notification: {e}")

@receiver(post_delete, sender='payments.Payment')
def payment_deleted(sender, instance, **kwargs):
    """Send payment deletion notification via WebSocket."""
    try:
        payload = {
            'event': 'payment_deleted',
            'payment': {
                'id': instance.id,
                'order_id': instance.order.id if instance.order else None,
            }
        }
        
        send_websocket_notification('transaction_updates', 'transaction_update', payload)
        
        logger.info(f"Payment deletion WebSocket notification sent: {instance.id}")
        
    except Exception as e:
        logger.error(f"Error sending payment deletion WebSocket notification: {e}")

# Broadcast utility function
def send_broadcast_message(message, message_type='info'):
    """Send broadcast message to all connected clients."""
    try:
        payload = {
            'event': 'broadcast',
            'message': message,
            'type': message_type,
            'timestamp': timezone.now().isoformat()
        }
        
        send_websocket_notification('broadcast', 'broadcast_message', payload)
        
        logger.info(f"Broadcast message sent: {message}")
        
    except Exception as e:
        logger.error(f"Error sending broadcast message: {e}")

# User notification utility function
def send_user_notification(user_id, message, notification_type='info'):
    """Send notification to specific user."""
    try:
        payload = {
            'event': 'user_notification',
            'message': message,
            'type': notification_type,
            'timestamp': timezone.now().isoformat()
        }
        
        send_websocket_notification(f'user_{user_id}', 'user_notification', payload)
        
        logger.info(f"User notification sent to user {user_id}: {message}")
        
    except Exception as e:
        logger.error(f"Error sending user notification: {e}")
