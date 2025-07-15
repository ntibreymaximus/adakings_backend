#!/usr/bin/env python
"""
Enable WAL mode for SQLite database to improve concurrency.
This script should be run after database migrations.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')

import django
django.setup()

from django.conf import settings
from django.db import connection

def enable_wal_mode():
    """Enable WAL mode for SQLite database."""
    try:
        # Get database path from settings
        db_path = settings.DATABASES['default']['NAME']
        
        print(f"Enabling WAL mode for database: {db_path}")
        
        # Connect directly to SQLite to enable WAL mode
        conn = sqlite3.connect(db_path)
        
        # Check current journal mode
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        current_mode = cursor.fetchone()[0]
        print(f"Current journal mode: {current_mode}")
        
        # Enable WAL mode
        cursor.execute("PRAGMA journal_mode=WAL;")
        new_mode = cursor.fetchone()[0]
        print(f"New journal mode: {new_mode}")
        
        # Set other optimizations
        cursor.execute("PRAGMA synchronous=NORMAL;")  # Better performance than FULL
        cursor.execute("PRAGMA cache_size=10000;")    # Increase cache size
        cursor.execute("PRAGMA temp_store=MEMORY;")   # Use memory for temporary tables
        
        # Verify settings
        cursor.execute("PRAGMA synchronous;")
        sync_mode = cursor.fetchone()[0]
        print(f"Synchronous mode: {sync_mode}")
        
        cursor.execute("PRAGMA cache_size;")
        cache_size = cursor.fetchone()[0]
        print(f"Cache size: {cache_size}")
        
        cursor.execute("PRAGMA temp_store;")
        temp_store = cursor.fetchone()[0]
        print(f"Temp store: {temp_store}")
        
        conn.close()
        
        print("WAL mode enabled successfully!")
        print("This will improve concurrency for SQLite operations.")
        
    except Exception as e:
        print(f"Error enabling WAL mode: {e}")
        return False
    
    return True

if __name__ == "__main__":
    enable_wal_mode()
