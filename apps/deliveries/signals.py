from django.db.models.signals import post_save, pre_save, post_delete, post_migrate
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Count, Q
from django.core.management import call_command
from .models import OrderAssignment
import logging
import os

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=OrderAssignment)
def track_assignment_status_change(sender, instance, **kwargs):
    """Track status changes before save"""
    if instance.pk:
        try:
            old_instance = OrderAssignment.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except OrderAssignment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=OrderAssignment)
def update_rider_stats_on_assignment_change(sender, instance, created, **kwargs):
    """Update rider statistics when assignment status changes"""
    if not instance.rider:
        logger.warning(f"Assignment {instance.id} has no rider assigned")
        return
    
    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status
    
    # Skip if status hasn't changed
    if old_status == new_status and not created:
        logger.debug(f"Assignment {instance.id} status unchanged at {new_status}")
        return
    
    logger.info(f"Assignment {instance.id} for order {instance.order.order_number} status changed from {old_status} to {new_status} (created={created})")
    
    # For critical status changes (delivered, returned, cancelled), 
    # always recalculate from database to ensure accuracy
    if new_status in ['delivered', 'returned', 'cancelled']:
        # Log before recalculation
        logger.info(f"Before recalculation - Rider {instance.rider.name}: current_orders={instance.rider.current_orders}, total_deliveries={instance.rider.total_deliveries}")
        
        recalculate_rider_stats(instance.rider)
        
        # Update order status if delivered
        if new_status == 'delivered':
            from apps.orders.models import Order
            try:
                    # Only update if order status is a valid status and not already fulfilled
                    valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
                    logger.info(f"Order {instance.order.order_number} current status: '{instance.order.status}', valid statuses: {valid_statuses}")
                    if instance.order.status in valid_statuses and instance.order.status != Order.STATUS_FULFILLED:
                        # Set flag to prevent circular update from order signal
                        instance.order._updating_from_delivery = True
                        instance.order.status = Order.STATUS_FULFILLED
                        # Use update_fields to skip validation and avoid triggering full save logic
                        instance.order.save(update_fields=['status', 'updated_at'])
                        logger.info(f"Order {instance.order.order_number} marked as Fulfilled")
                    elif instance.order.status not in valid_statuses:
                        logger.warning(f"Order {instance.order.order_number} has invalid status '{instance.order.status}'. Using direct database update.")
                        # Direct database update to fix invalid status
                        Order.objects.filter(pk=instance.order.pk).update(status=Order.STATUS_FULFILLED)
                        logger.info(f"Order {instance.order.order_number} status updated directly to Fulfilled")
            except Exception as e:
                logger.error(f"Error updating order status for {instance.order.order_number}: {str(e)}")
            
            # Update timestamp if needed
            if not instance.delivered_at:
                instance.delivered_at = timezone.now()
                instance.save(update_fields=['delivered_at'])
        
        # Refresh rider instance to get updated values
        instance.rider.refresh_from_db()
        logger.info(f"After recalculation - Rider {instance.rider.name}: current_orders={instance.rider.current_orders}, total_deliveries={instance.rider.total_deliveries}")
        logger.info(f"Order {new_status}: Successfully updated stats for rider {instance.rider.name}")
        return
    
    # Handle new assignment
    if created and new_status in ['assigned', 'accepted']:
        old_count = instance.rider.current_orders
        instance.rider.current_orders += 1
        instance.rider.save(update_fields=['current_orders', 'updated_at'])
        logger.info(f"Incremented current_orders for rider {instance.rider.name} from {old_count} to {instance.rider.current_orders}")
    
    # Handle status transitions
    elif old_status and old_status != new_status:
        # Order picked up
        if new_status == 'picked_up' and not instance.picked_up_at:
            instance.picked_up_at = timezone.now()
            instance.save(update_fields=['picked_up_at'])


def recalculate_rider_stats(rider):
    """Recalculate rider statistics from actual database records"""
    from .models import OrderAssignment, DailyDeliveryStats
    
    # Count current active orders
    current_count = OrderAssignment.objects.filter(
        rider=rider,
        status__in=['assigned', 'accepted', 'picked_up', 'in_transit']
    ).count()
    
    # Count completed deliveries
    delivered_count = OrderAssignment.objects.filter(
        rider=rider,
        status__in=['delivered', 'returned']
    ).count()
    
    # Count today's deliveries
    today = timezone.now().date()
    today_count = OrderAssignment.objects.filter(
        rider=rider,
        status__in=['delivered', 'returned'],
        delivered_at__date=today
    ).count()
    
    # Update rider stats if they've changed
    if rider.current_orders != current_count or rider.total_deliveries != delivered_count or rider.today_deliveries != today_count:
        rider.current_orders = current_count
        rider.total_deliveries = delivered_count
        rider.today_deliveries = today_count
        rider.save(update_fields=['current_orders', 'total_deliveries', 'today_deliveries'])
        logger.info(f"Recalculated stats for {rider.name}: current={current_count}, total={delivered_count}, today={today_count}")
        
        # Also update or create daily stats record
        DailyDeliveryStats.objects.update_or_create(
            rider=rider,
            date=today,
            defaults={'deliveries_count': today_count}
        )


@receiver(post_delete, sender=OrderAssignment)
def update_rider_stats_on_assignment_delete(sender, instance, **kwargs):
    """Update rider statistics when an assignment is deleted"""
    if instance.rider:
        logger.info(f"Assignment deleted for order {instance.order.order_number} - updating rider {instance.rider.name} stats")
        
        # Recalculate rider stats after deletion
        recalculate_rider_stats(instance.rider)
        
        # Refresh rider instance to get updated values
        instance.rider.refresh_from_db()
        logger.info(f"After deletion - Rider {instance.rider.name}: current_orders={instance.rider.current_orders}, total_deliveries={instance.rider.total_deliveries}")


@receiver(post_migrate)
def load_delivery_locations_on_migrate(sender, **kwargs):
    """Load delivery locations from file after migrations"""
    # Only run this for the deliveries app
    if sender.name == 'apps.deliveries':
        # Check if we're not in a testing environment
        if not os.environ.get('TESTING'):
            try:
                # Delay execution to ensure database is ready
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                
                # Now load the delivery locations
                call_command('load_delivery_locations', '--update')
                logger.info("Delivery locations loaded successfully after migration")
            except Exception as e:
                logger.warning(f"Could not load delivery locations on startup: {e}")
