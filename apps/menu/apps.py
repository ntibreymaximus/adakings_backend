from django.apps import AppConfig
import threading
import time
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

class MenuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.menu'
    verbose_name = 'Menu Management'

    _sync_thread = None
    _stop_sync = threading.Event()

    def ready(self):
        # Import signals to register them
        import apps.menu.signals

        # Start the periodic sync thread only in the main process
        import os
        if os.environ.get('RUN_MAIN') == 'true' or not os.environ.get('WERKZEUG_RUN_MAIN'):
            self.start_periodic_sync()

    def start_periodic_sync(self):
        """Start the background thread for periodic menu sync"""
        if self._sync_thread is None or not self._sync_thread.is_alive():
            self._stop_sync.clear()
            self._sync_thread = threading.Thread(
                target=self._periodic_sync_worker,
                daemon=True,
                name='MenuSyncThread'
            )
            self._sync_thread.start()
            logger.info("Started menu periodic sync thread")

    def _periodic_sync_worker(self):
        """Worker thread that syncs menu items every 6 hours"""
        logger.info("Menu sync worker started")

        from django.core.management import call_command
        
        # Initial sync on startup - clear and reload menu
        try:
            logger.info("Performing initial menu sync...")
            call_command('load_menu_items', '--clear')
            logger.info("Initial menu sync completed")
        except Exception as e:
            logger.error(f"Initial menu sync failed: {e}")

        # Run periodic syncs every 6 hours
        while not self._stop_sync.is_set():
            # Wait for 6 hours or until stop signal
            if self._stop_sync.wait(6 * 3600):  # 6 hours in seconds
                break

            # Perform sync - always clear and reload
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"[{timestamp}] Starting scheduled menu sync...")
                call_command('load_menu_items', '--clear')
                logger.info(f"[{timestamp}] Scheduled menu sync completed")
            except Exception as e:
                logger.error(f"Scheduled menu sync failed: {e}")

        logger.info("Menu sync worker stopped")
