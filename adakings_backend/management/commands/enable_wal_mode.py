from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Enable WAL mode on SQLite database for better concurrency'

    def handle(self, *args, **options):
        # Only run for SQLite databases
        if 'sqlite3' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(self.style.WARNING('This command only works with SQLite databases'))
            return
        
        try:
            with connection.cursor() as cursor:
                # Check current journal mode
                cursor.execute("PRAGMA journal_mode;")
                current_mode = cursor.fetchone()[0]
                self.stdout.write(f'Current journal mode: {current_mode}')
                
                if current_mode == 'wal':
                    self.stdout.write(self.style.SUCCESS('WAL mode is already enabled'))
                else:
                    # Enable WAL mode
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    new_mode = cursor.fetchone()[0]
                    
                    if new_mode == 'wal':
                        self.stdout.write(self.style.SUCCESS('Successfully enabled WAL mode'))
                    else:
                        self.stdout.write(self.style.ERROR(f'Failed to enable WAL mode, current mode: {new_mode}'))
                
                # Set other pragmas for better performance
                cursor.execute("PRAGMA synchronous=NORMAL;")
                cursor.execute("PRAGMA temp_store=MEMORY;")
                cursor.execute("PRAGMA mmap_size=30000000000;")
                
                # Show current settings
                cursor.execute("PRAGMA synchronous;")
                sync_mode = cursor.fetchone()[0]
                self.stdout.write(f'Synchronous mode: {sync_mode}')
                
                cursor.execute("PRAGMA temp_store;")
                temp_store = cursor.fetchone()[0]
                self.stdout.write(f'Temp store: {temp_store}')
                
                self.stdout.write(self.style.SUCCESS('\nSQLite optimization complete'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
