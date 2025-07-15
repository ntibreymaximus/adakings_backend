#!/usr/bin/env python
"""
Utility to fix SQLite database locking issues
"""

import os
import sys
import sqlite3
import time
import shutil
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_database_lock():
    """Fix SQLite database lock by closing connections and enabling WAL mode"""
    
    db_path = Path('db.sqlite3')
    
    if not db_path.exists():
        print("Database file not found!")
        return False
    
    try:
        # First, make a backup
        backup_path = Path(f'db.sqlite3.backup.{int(time.time())}')
        print(f"Creating backup at {backup_path}")
        shutil.copy2(db_path, backup_path)
        
        # Close any existing Django connections
        try:
            from django.db import connections
            for conn in connections.all():
                conn.close()
            print("Closed all Django database connections")
        except:
            pass
        
        # Connect directly to SQLite
        print("Connecting to SQLite database...")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check current journal mode
        cursor.execute("PRAGMA journal_mode;")
        current_mode = cursor.fetchone()[0]
        print(f"Current journal mode: {current_mode}")
        
        # Enable WAL mode
        cursor.execute("PRAGMA journal_mode=WAL;")
        new_mode = cursor.fetchone()[0]
        print(f"New journal mode: {new_mode}")
        
        # Set other optimizations
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        cursor.execute("PRAGMA cache_size=-64000;")  # 64MB cache
        cursor.execute("PRAGMA busy_timeout=30000;")  # 30 second timeout
        
        # Checkpoint to clean up WAL file
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        
        conn.commit()
        conn.close()
        
        print("Database optimization complete!")
        
        # Clean up any lock files
        for lock_file in ['db.sqlite3-journal', 'db.sqlite3-wal', 'db.sqlite3-shm']:
            lock_path = Path(lock_file)
            if lock_path.exists() and lock_path.stat().st_size == 0:
                print(f"Removing empty lock file: {lock_file}")
                lock_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("SQLite Database Lock Fixer")
    print("=" * 50)
    
    # Kill any running Django processes
    print("\nPlease ensure all Django processes are stopped.")
    print("Press Ctrl+C in any running Django servers.")
    
    input("\nPress Enter when ready to continue...")
    
    if fix_database_lock():
        print("\n✓ Database lock fixed successfully!")
        print("You can now start the Django server again.")
    else:
        print("\n✗ Failed to fix database lock.")
        print("You may need to restart your computer or restore from backup.")
