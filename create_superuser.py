#!/usr/bin/env python
"""
Script to create a Django superuser programmatically
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

from django.contrib.auth import get_user_model

User = get_user_model()

# Superuser credentials
username = 'admin'
email = 'admin@adakings.com'
password = 'AdakingsAdmin2025!'

try:
    # Check if superuser already exists
    if User.objects.filter(username=username).exists():
        print(f"❌ Superuser '{username}' already exists!")
        sys.exit(1)
    
    # Create superuser
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    
    print(f"✅ Superuser '{username}' created successfully!")
    print(f"✅ Email: {email}")
    print(f"✅ Login at: /admin/")
    print("🔒 Please change the password after first login!")
    
except Exception as e:
    print(f"❌ Failed to create superuser: {e}")
    sys.exit(1)
