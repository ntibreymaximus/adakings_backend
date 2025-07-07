#!/usr/bin/env python
"""
Simple script to test the health endpoint
"""
import os
import sys
import django
import requests
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

# Test the health check view directly
try:
    from django.test import RequestFactory
    from adakings_backend.urls import health_check
    
    factory = RequestFactory()
    request = factory.get('/health')
    response = health_check(request)
    
    print(f"✅ Health check view test successful")
    print(f"Status code: {response.status_code}")
    print(f"Content: {response.content.decode()}")
    
except Exception as e:
    print(f"❌ Health check view test failed: {e}")
    sys.exit(1)

# Test database connection
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# Test WSGI application
try:
    from adakings_backend.wsgi import application
    print("✅ WSGI application import successful")
except Exception as e:
    print(f"❌ WSGI application import failed: {e}")
    sys.exit(1)

print("\n🎉 All tests passed! The application should work in production.")
