#!/usr/bin/env python
"""
Environment Configuration Checker
Verifies that Django is using the correct environment settings.
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

from django.conf import settings

def check_environment():
    """Check and display current Django environment configuration."""
    print("=" * 60)
    print("🔍 DJANGO ENVIRONMENT CONFIGURATION CHECK")
    print("=" * 60)
    
    # Environment variables
    print("\n📋 Environment Variables:")
    print(f"   DJANGO_DEBUG: {os.environ.get('DJANGO_DEBUG', 'Not Set')}")
    print(f"   DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not Set')}")
    print(f"   DJANGO_ENVIRONMENT: {os.environ.get('DJANGO_ENVIRONMENT', 'Not Set')}")
    print(f"   DATABASE_ENGINE: {os.environ.get('DATABASE_ENGINE', 'Not Set')}")
    print(f"   RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'Not Set')}")
    
    # Django settings
    print("\n⚙️  Django Settings:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   SETTINGS_MODULE: {settings.SETTINGS_MODULE}")
    print(f"   DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
    print(f"   DATABASE NAME: {settings.DATABASES['default']['NAME']}")
    print(f"   DATABASE HOST: {settings.DATABASES['default']['HOST']}")
    print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    
    # Logging configuration
    print(f"\n📝 Logging Configuration:")
    has_filters = bool(settings.LOGGING.get('filters', {}))
    print(f"   Has Custom Filters: {has_filters}")
    console_level = settings.LOGGING['handlers']['console']['level']
    print(f"   Console Log Level: {console_level}")
    
    # Environment determination
    print(f"\n🎯 Environment Determination:")
    if settings.DEBUG:
        env_type = "DEVELOPMENT"
        print(f"   Environment: {env_type} ⚠️")
        print("   ⚠️  WARNING: DEBUG=True in what should be production!")
    else:
        env_type = "PRODUCTION"
        print(f"   Environment: {env_type} ✅")
        print("   ✅ Correct production configuration")
    
    # Security settings
    print(f"\n🔒 Security Settings:")
    print(f"   SECURE_SSL_REDIRECT: {getattr(settings, 'SECURE_SSL_REDIRECT', False)}")
    print(f"   SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', False)}")
    print(f"   CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', False)}")
    
    print("=" * 60)
    return env_type == "PRODUCTION"

if __name__ == '__main__':
    try:
        is_production = check_environment()
        if is_production:
            print("✅ Environment configuration is correct for production!")
            sys.exit(0)
        else:
            print("❌ Environment configuration issues detected!")
            sys.exit(1)
    except Exception as e:
        print(f"💥 Error checking environment: {str(e)}")
        sys.exit(1)
