#!/usr/bin/env python
"""
Environment Configuration Checker
Verifies that Django is using the correct environment settings and variables.
"""

import os
import sys
import django
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
django.setup()

from django.conf import settings

def check_environment():
    """Check and display current Django environment configuration."""
    print("=" * 70)
    print("🔍 DJANGO ENVIRONMENT CONFIGURATION CHECK")
    print("=" * 70)
    
    # Detect environment
    is_railway = 'RAILWAY_ENVIRONMENT' in os.environ
    django_env = os.environ.get('DJANGO_ENVIRONMENT', 'local')
    
    print(f"\n🌍 Environment Detection:")
    print(f"   Is Railway: {is_railway}")
    print(f"   Django Environment: {django_env}")
    print(f"   Environment Type: {'Railway' if is_railway else 'Local'}")
    
    # Environment variables
    print("\n📋 Environment Variables:")
    print(f"   DJANGO_DEBUG: {os.environ.get('DJANGO_DEBUG', 'Not Set')}")
    print(f"   DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not Set')}")
    print(f"   DJANGO_ENVIRONMENT: {os.environ.get('DJANGO_ENVIRONMENT', 'Not Set')}")
    print(f"   RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'Not Set')}")
    
    # Database configuration
    print("\n🗄️  Database Configuration:")
    db_config = settings.DATABASES['default']
    print(f"   ENGINE: {db_config['ENGINE']}")
    print(f"   NAME: {db_config['NAME']}")
    
    if 'postgresql' in db_config['ENGINE']:
        print(f"   HOST: {db_config.get('HOST', 'Not Set')}")
        print(f"   PORT: {db_config.get('PORT', 'Not Set')}")
        print(f"   USER: {db_config.get('USER', 'Not Set')}")
        print(f"   PASSWORD: {'***' if db_config.get('PASSWORD') else 'Not Set'}")
        
        # Check Railway PostgreSQL variables
        if is_railway:
            print("\n   Railway PostgreSQL Variables:")
            print(f"     PGDATABASE: {os.environ.get('PGDATABASE', 'Not Set')}")
            print(f"     PGHOST: {os.environ.get('PGHOST', 'Not Set')}")
            print(f"     PGPORT: {os.environ.get('PGPORT', 'Not Set')}")
            print(f"     PGUSER: {os.environ.get('PGUSER', 'Not Set')}")
            print(f"     PGPASSWORD: {'***' if os.environ.get('PGPASSWORD') else 'Not Set'}")
    
    # Django settings
    print("\n⚙️  Django Settings:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   SETTINGS_MODULE: {settings.SETTINGS_MODULE}")
    print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    
    # Security settings
    print(f"\n🔒 Security Settings:")
    print(f"   SECURE_SSL_REDIRECT: {getattr(settings, 'SECURE_SSL_REDIRECT', False)}")
    print(f"   SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', False)}")
    print(f"   CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', False)}")
    print(f"   SECURE_HSTS_SECONDS: {getattr(settings, 'SECURE_HSTS_SECONDS', 0)}")
    
    # Environment file check
    print(f"\n📄 Environment File Check:")
    if not is_railway:
        env_file = Path('.env')
        if env_file.exists():
            print(f"   .env file: ✅ Found")
        else:
            print(f"   .env file: ❌ Missing (required for local development)")
    else:
        print(f"   .env file: Not needed (using Railway environment variables)")
    
    # Validate environment configuration
    print(f"\n✅ Environment Validation:")
    
    validation_passed = True
    
    if is_railway:
        # Railway environment validation
        required_vars = ['PGDATABASE', 'PGHOST', 'PGUSER', 'PGPASSWORD']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"   ❌ Missing Railway variables: {', '.join(missing_vars)}")
            validation_passed = False
        else:
            print(f"   ✅ All Railway PostgreSQL variables are set")
            
        if 'postgresql' not in db_config['ENGINE']:
            print(f"   ❌ Railway should use PostgreSQL, but using: {db_config['ENGINE']}")
            validation_passed = False
        else:
            print(f"   ✅ Using PostgreSQL database as expected")
            
    else:
        # Local environment validation
        if not Path('.env').exists():
            print(f"   ❌ .env file missing for local development")
            validation_passed = False
        else:
            print(f"   ✅ .env file found for local development")
            
        if 'sqlite' not in db_config['ENGINE']:
            print(f"   ❌ Local should use SQLite, but using: {db_config['ENGINE']}")
            validation_passed = False
        else:
            print(f"   ✅ Using SQLite database as expected")
    
    # Environment type determination
    print(f"\n🎯 Environment Summary:")
    if is_railway:
        if django_env == 'production':
            env_type = "PRODUCTION"
            print(f"   Environment: {env_type} (Railway) 🚀")
            if settings.DEBUG:
                print(f"   ⚠️  WARNING: DEBUG=True in production environment!")
                validation_passed = False
        else:
            env_type = "DEVELOPMENT"
            print(f"   Environment: {env_type} (Railway) 🔧")
    else:
        env_type = "LOCAL"
        print(f"   Environment: {env_type} (Development) 💻")
    
    print("=" * 70)
    return validation_passed, env_type

if __name__ == '__main__':
    try:
        validation_passed, env_type = check_environment()
        
        if validation_passed:
            print(f"\n✅ Environment configuration is correct for {env_type}!")
            print(f"🎉 All required variables are properly set.")
            sys.exit(0)
        else:
            print(f"\n❌ Environment configuration issues detected in {env_type}!")
            print(f"⚠️  Please fix the issues above before proceeding.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error checking environment: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
