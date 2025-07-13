#!/usr/bin/env python
"""
Check CORS and Debug settings for the Adakings Backend
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.conf import settings

print("="*60)
print("DJANGO CONFIGURATION CHECK")
print("="*60)

# Debug settings
print("\n1. DEBUG SETTINGS:")
print(f"   DEBUG: {settings.DEBUG}")
print(f"   ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"   IS_RAILWAY: {settings.IS_RAILWAY}")
print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

# CORS settings
print("\n2. CORS SETTINGS:")
if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS'):
    print(f"   CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}")
if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
    print(f"   CORS_ALLOWED_ORIGINS: {getattr(settings, 'CORS_ALLOWED_ORIGINS', 'Not set')}")
print(f"   CORS_ALLOW_CREDENTIALS: {settings.CORS_ALLOW_CREDENTIALS}")
if hasattr(settings, 'CORS_ALLOW_HEADERS'):
    print(f"   CORS_ALLOW_HEADERS: {settings.CORS_ALLOW_HEADERS}")

# CSRF settings
print("\n3. CSRF SETTINGS:")
print(f"   CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")
print(f"   CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
print(f"   CSRF_COOKIE_SAMESITE: {settings.CSRF_COOKIE_SAMESITE}")

# Authentication settings
print("\n4. AUTHENTICATION SETTINGS:")
print(f"   DEFAULT_AUTHENTICATION_CLASSES: {settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', 'Not set')}")
print(f"   DEFAULT_PERMISSION_CLASSES: {settings.REST_FRAMEWORK.get('DEFAULT_PERMISSION_CLASSES', 'Not set')}")

# JWT settings
print("\n5. JWT SETTINGS:")
print(f"   ACCESS_TOKEN_LIFETIME: {settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', 'Not set')}")
print(f"   REFRESH_TOKEN_LIFETIME: {settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', 'Not set')}")

# Check middleware
print("\n6. MIDDLEWARE ORDER:")
for i, middleware in enumerate(settings.MIDDLEWARE):
    print(f"   {i+1}. {middleware}")

# Environment variables
print("\n7. ENVIRONMENT VARIABLES:")
print(f"   DJANGO_DEBUG (env): {os.environ.get('DJANGO_DEBUG', 'Not set')}")
print(f"   DJANGO_ENVIRONMENT (env): {os.environ.get('DJANGO_ENVIRONMENT', 'Not set')}")
print(f"   CORS_ALLOWED_ORIGINS (env): {os.environ.get('CORS_ALLOWED_ORIGINS', 'Not set')}")

print("\n" + "="*60)
