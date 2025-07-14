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
        
        # Initial sync on startup - clear and reload
        try:
            logger.info("Performing initial delivery location sync...")
            call_command('load_delivery_locations', '--clear')
            logger.info("Initial delivery location sync completed")
        except Exception as e:
            logger.error(f"Initial delivery location sync failed: {e}")
        
        # Run periodic syncs every 6 hours
        while not self._stop_sync.is_set():
            # Wait for 6 hours or until stop signal
            if self._stop_sync.wait(6 * 3600):  # 6 hours in seconds
                break
            
            # Perform sync - always clear and reload
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"[{timestamp}] Starting scheduled delivery location sync...")
                call_command('load_delivery_locations', '--clear')
                logger.info(f"[{timestamp}] Scheduled delivery location sync completed")
            except Exception as e:
                logger.error(f"Scheduled delivery location sync failed: {e}")
        
        logger.info("Delivery location sync worker stopped")
