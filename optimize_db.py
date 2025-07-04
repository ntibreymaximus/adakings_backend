#!/usr/bin/env python
"""
Database Optimization Script for Instant Queries
Applies various optimizations to improve database performance
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line


def optimize_sqlite():
    """Apply SQLite-specific optimizations for instant queries"""
    print("Applying SQLite optimizations...")
    
    with connection.cursor() as cursor:
        # Enable WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL;")
        
        # Optimize for speed over safety (acceptable for development)
        cursor.execute("PRAGMA synchronous=NORMAL;")
        
        # Increase cache size for better performance
        cursor.execute("PRAGMA cache_size=10000;")
        
        # Store temporary tables in memory
        cursor.execute("PRAGMA temp_store=MEMORY;")
        
        # Enable memory mapping for faster file access
        cursor.execute("PRAGMA mmap_size=134217728;")  # 128MB
        
        # Optimize foreign key checks
        cursor.execute("PRAGMA foreign_keys=ON;")
        
        # Set page size for better performance
        cursor.execute("PRAGMA page_size=4096;")
        
        # Auto vacuum for maintenance
        cursor.execute("PRAGMA auto_vacuum=INCREMENTAL;")
        
        print("SQLite optimizations applied successfully!")


def analyze_database():
    """Analyze database tables for query optimization"""
    print("Analyzing database for optimization opportunities...")
    
    with connection.cursor() as cursor:
        # Analyze all tables for better query planning
        cursor.execute("ANALYZE;")
        
        print("Database analysis completed!")


def create_missing_indexes():
    """Create additional indexes for better performance"""
    print("Creating additional performance indexes...")
    
    with connection.cursor() as cursor:
        try:
            # Additional composite indexes for common query patterns
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_status_created 
                ON orders_order(status, created_at DESC);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_delivery_status 
                ON orders_order(delivery_type, status);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_payments_order_status 
                ON payments_payment(order_id, status, payment_type);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_payment_status 
                ON payments_paymenttransaction(payment_id, status, is_verified);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_orderitems_order_menu 
                ON orders_orderitem(order_id, menu_item_id);
            """)
            
            print("Additional indexes created successfully!")
            
        except Exception as e:
            print(f"Some indexes may already exist: {e}")


def vacuum_database():
    """Vacuum the database to reclaim space and optimize"""
    print("Vacuuming database...")
    
    with connection.cursor() as cursor:
        cursor.execute("VACUUM;")
        
        print("Database vacuum completed!")


def main():
    """Run all optimization steps"""
    print("🚀 Starting Database Optimization for Instant Queries...")
    print("=" * 60)
    
    try:
        # Apply SQLite optimizations
        optimize_sqlite()
        print()
        
        # Create missing indexes
        create_missing_indexes()
        print()
        
        # Analyze database
        analyze_database()
        print()
        
        # Vacuum database
        vacuum_database()
        print()
        
        print("=" * 60)
        print("✅ Database optimization completed successfully!")
        print()
        print("Benefits applied:")
        print("• WAL mode enabled for better concurrent access")
        print("• Memory cache increased to 10,000 pages")
        print("• Temporary tables stored in memory")
        print("• Memory mapping enabled (128MB)")
        print("• Additional composite indexes created")
        print("• Database analyzed for query optimization")
        print("• Database vacuumed for space optimization")
        print()
        print("Your database should now provide instant query responses!")
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
