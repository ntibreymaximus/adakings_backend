import time
import threading
import signal
import sys
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Continuously sync delivery locations from file every 6 hours'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_stop = threading.Event()
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=6,
            help='Interval in hours between syncs (default: 6)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run sync once and exit'
        )
    
    def handle(self, *args, **options):
        interval_hours = options['interval']
        run_once = options['once']
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.stdout.write(self.style.SUCCESS(
            f"Starting delivery location sync service (interval: {interval_hours} hours)"
        ))
        
        # Run the first sync immediately
        self._sync_locations()
        
        if run_once:
            return
        
        # Continue running periodic syncs
        while not self.should_stop.is_set():
            try:
                # Wait for the specified interval or until stop signal
                self.should_stop.wait(interval_hours * 3600)  # Convert hours to seconds
                
                if not self.should_stop.is_set():
                    self._sync_locations()
                    
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
        
        self.stdout.write(self.style.WARNING("Delivery location sync service stopped"))
    
    def _sync_locations(self):
        """Perform the actual sync"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.stdout.write(f"\n[{timestamp}] Syncing delivery locations...")
        
        try:
            # Call the load command with update flag
            call_command('load_delivery_locations', '--update')
            self.stdout.write(self.style.SUCCESS(f"[{timestamp}] Sync completed successfully"))
            logger.info("Delivery locations synced successfully")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[{timestamp}] Sync failed: {e}"))
            logger.error(f"Failed to sync delivery locations: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.stdout.write(self.style.WARNING("\nReceived stop signal, shutting down..."))
        self.should_stop.set()
        sys.exit(0)
