"""
Django management command to clean up SQLite WAL files and optimize database
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os
import sqlite3


class Command(BaseCommand):
    help = 'Clean up SQLite WAL files and optimize database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Run VACUUM to optimize database file',
        )
        parser.add_argument(
            '--checkpoint',
            action='store_true',
            help='Force WAL checkpoint to main database',
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Run ANALYZE to update query planner statistics',
        )

    def handle(self, *args, **options):
        # Check if we're using SQLite
        if 'sqlite' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(
                self.style.WARNING('This command only works with SQLite databases.')
            )
            return

        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            self.stdout.write(
                self.style.ERROR(f'Database file not found: {db_path}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Working with database: {db_path}')
        )

        try:
            # Close existing Django connections
            connection.close()
            
            # Connect directly to SQLite
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Force WAL checkpoint
            if options['checkpoint'] or not any([options['vacuum'], options['analyze']]):
                self.stdout.write('Performing WAL checkpoint...')
                cursor.execute('PRAGMA wal_checkpoint(TRUNCATE);')
                result = cursor.fetchone()
                self.stdout.write(
                    self.style.SUCCESS(f'WAL checkpoint result: {result}')
                )

            # Vacuum database
            if options['vacuum']:
                self.stdout.write('Vacuuming database...')
                cursor.execute('VACUUM;')
                self.stdout.write(
                    self.style.SUCCESS('Database vacuum completed')
                )

            # Analyze database
            if options['analyze']:
                self.stdout.write('Analyzing database...')
                cursor.execute('ANALYZE;')
                self.stdout.write(
                    self.style.SUCCESS('Database analysis completed')
                )

            # Get database info
            cursor.execute('PRAGMA page_count;')
            page_count = cursor.fetchone()[0]
            
            cursor.execute('PRAGMA page_size;')
            page_size = cursor.fetchone()[0]
            
            cursor.execute('PRAGMA freelist_count;')
            free_pages = cursor.fetchone()[0]
            
            db_size_mb = (page_count * page_size) / (1024 * 1024)
            free_space_mb = (free_pages * page_size) / (1024 * 1024)

            self.stdout.write('\n' + '='*50)
            self.stdout.write('DATABASE STATISTICS:')
            self.stdout.write(f'  Total pages: {page_count:,}')
            self.stdout.write(f'  Page size: {page_size:,} bytes')
            self.stdout.write(f'  Free pages: {free_pages:,}')
            self.stdout.write(f'  Database size: {db_size_mb:.2f} MB')
            self.stdout.write(f'  Free space: {free_space_mb:.2f} MB')
            self.stdout.write('='*50)

            conn.close()

            # Check auxiliary files
            wal_file = f"{db_path}-wal"
            shm_file = f"{db_path}-shm"
            
            self.stdout.write('\nAUXILIARY FILES:')
            
            if os.path.exists(wal_file):
                wal_size = os.path.getsize(wal_file) / 1024
                self.stdout.write(f'  WAL file: {wal_size:.2f} KB')
            else:
                self.stdout.write('  WAL file: Not present')
                
            if os.path.exists(shm_file):
                shm_size = os.path.getsize(shm_file) / 1024
                self.stdout.write(f'  SHM file: {shm_size:.2f} KB')
            else:
                self.stdout.write('  SHM file: Not present')

            self.stdout.write(
                self.style.SUCCESS('\n✅ SQLite cleanup completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during cleanup: {str(e)}')
            )
        finally:
            # Ensure Django can reconnect
            connection.ensure_connection()

    def get_file_size_mb(self, filepath):
        """Get file size in MB"""
        if os.path.exists(filepath):
            return os.path.getsize(filepath) / (1024 * 1024)
        return 0
