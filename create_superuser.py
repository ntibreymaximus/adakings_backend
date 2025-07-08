#!/usr/bin/env python
"""
Superuser Auto-Creation Script for Railway Deployment

This script automatically creates a superuser account if none exists.
It's designed to run during Railway deployment to ensure admin access.
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from django.core.management.utils import get_random_secret_key

User = get_user_model()


def create_superuser_if_none_exists():
    """
    Create a superuser if no superusers exist in the database.
    Uses environment variables for credentials in production.
    """
    print("🔍 Checking for existing superusers...")
    
    # Check if any superusers exist
    superusers_count = User.objects.filter(is_superuser=True).count()
    
    if superusers_count > 0:
        print(f"✅ Found {superusers_count} existing superuser(s). Skipping creation.")
        return True
    
    print("🚀 No superusers found. Creating default superuser...")
    
    # Get credentials from environment variables
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'superadmin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@adakings.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    
    # Generate a secure password if none provided
    if not password:
        password = get_random_secret_key()
        print(f"⚠️  No DJANGO_SUPERUSER_PASSWORD provided. Generated secure password.")
        print(f"🔑 Generated password: {password}")
        print("🔒 IMPORTANT: Save this password securely and change it after first login!")
    
    try:
        # Create the superuser
        superuser = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role='superadmin'  # Ensure superadmin role
        )
        
        print(f"✅ Superuser created successfully!")
        print(f"   🔸 Username: {superuser.username}")
        print(f"   🔸 Email: {superuser.email}")
        print(f"   🔸 Role: {superuser.get_role_display()}")
        print(f"   🔸 Staff ID: {superuser.staff_id}")
        print(f"   🔸 Is Staff: {superuser.is_staff}")
        print(f"   🔸 Is Superuser: {superuser.is_superuser}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create superuser: {str(e)}")
        return False


def main():
    """Main function to run the superuser creation process."""
    print("=" * 60)
    print("🔐 ADAKINGS SUPERUSER AUTO-CREATION")
    print("=" * 60)
    
    try:
        success = create_superuser_if_none_exists()
        
        if success:
            print("=" * 60)
            print("✅ Superuser setup completed successfully!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("=" * 60)
            print("❌ Superuser setup failed!")
            print("=" * 60)
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Critical error during superuser creation: {str(e)}")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
