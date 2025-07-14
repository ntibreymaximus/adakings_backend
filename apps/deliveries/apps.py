from django.apps import AppConfig
import threading
import time
import logging

logger = logging.getLogger(__name__)


class DeliveriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.deliveries'
    _sync_thread = None
    _stop_sync = threading.Event()
    
    def ready(self):
        import apps.deliveries.signals
        
        # Start the periodic sync thread only in the main process
        # Avoid starting multiple threads in development reloader
        import os
        if os.environ.get('RUN_MAIN') == 'true' or not os.environ.get('WERKZEUG_RUN_MAIN'):
            self.start_periodic_sync()
    
    def start_periodic_sync(self):
        """Start the background thread for periodic location sync"""
        if self._sync_thread is None or not self._sync_thread.is_alive():
            self._stop_sync.clear()
            self._sync_thread = threading.Thread(
                target=self._periodic_sync_worker,
                daemon=True,
                name='DeliveryLocationSync'
            )
            self._sync_thread.start()
            logger.info("Started delivery location periodic sync thread")
    
    def _periodic_sync_worker(self):
        """Worker thread that syncs delivery locations every 6 hours"""
        from django.core.management import call_command
        from datetime import datetime
        
        logger.info("Delivery location sync worker started")
        
        # Initial sync on startup - preserve data first, then clear and reload
        try:
            logger.info("Performing initial delivery location sync...")
            # First ensure all orders have historical data before clearing
            self._preserve_order_delivery_history()
            call_command('load_delivery_locations', '--clear')
            logger.info("Initial delivery location sync completed")
        except Exception as e:
            logger.error(f"Initial delivery location sync failed: {e}")
        
        # Run periodic syncs every 6 hours
        while not self._stop_sync.is_set():
            # Wait for 6 hours or until stop signal
            if self._stop_sync.wait(6 * 3600):  # 6 hours in seconds
                break
            
            # Perform sync - preserve data first, then clear and reload
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"[{timestamp}] Starting scheduled delivery location sync...")
                # First ensure all orders have historical data before clearing
                self._preserve_order_delivery_history()
                call_command('load_delivery_locations', '--clear')
                logger.info(f"[{timestamp}] Scheduled delivery location sync completed")
            except Exception as e:
                logger.error(f"Scheduled delivery location sync failed: {e}")
        
        logger.info("Delivery location sync worker stopped")
    
    def _preserve_order_delivery_history(self):
        """Preserve delivery history for all orders before clearing locations"""
        from apps.orders.models import Order
        from apps.deliveries.models import DeliveryLocation
        from django.db import transaction
        
        logger.info("Preserving order delivery history before location sync...")
        
        with transaction.atomic():
            # First, preserve data for orders with delivery locations
            orders_with_location = Order.objects.filter(
                delivery_location__isnull=False
            ).select_related('delivery_location')
            
            preserved_count = 0
            for order in orders_with_location:
                if order.delivery_location and not order.delivery_location_name:
                    order.delivery_location_name = order.delivery_location.name
                    order.delivery_location_fee = order.delivery_location.fee
                    order.save(update_fields=['delivery_location_name', 'delivery_location_fee'])
                    preserved_count += 1
            
            # Also preserve for orders with custom locations
            custom_orders = Order.objects.filter(
                custom_delivery_location__isnull=False,
                delivery_location__isnull=True,
                delivery_location_name__isnull=True
            )
            
            for order in custom_orders:
                if order.custom_delivery_location:
                    order.delivery_location_name = order.custom_delivery_location
                    order.delivery_location_fee = order.custom_delivery_fee
                    order.save(update_fields=['delivery_location_name', 'delivery_location_fee'])
                    preserved_count += 1
            
            # Finally, preserve for orders with delivery fee but no name
            orders_with_fee = Order.objects.filter(
                delivery_type='Delivery',
                delivery_fee__gt=0,
                delivery_location_name__isnull=True
            )
            
            for order in orders_with_fee:
                if not order.delivery_location_fee:
                    order.delivery_location_fee = order.delivery_fee
                if not order.delivery_location_name:
                    # Try to determine name from fee
                    if order.delivery_fee == 0:
                        order.delivery_location_name = "Bolt Delivery"
                    elif order.delivery_fee == 5:
                        order.delivery_location_name = "Campus Delivery"
                    elif order.delivery_fee == 10:
                        order.delivery_location_name = "Near Campus Delivery" 
                    elif order.delivery_fee == 15:
                        order.delivery_location_name = "Off-Campus Delivery"
                    else:
                        order.delivery_location_name = f"Delivery (₵{order.delivery_fee})"
                order.save(update_fields=['delivery_location_name', 'delivery_location_fee'])
                preserved_count += 1
            
            if preserved_count > 0:
                logger.info(f"Preserved delivery history for {preserved_count} orders")
