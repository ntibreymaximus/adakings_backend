#!/usr/bin/env python3
"""
Test script to verify JWT token refresh functionality
Run this to check if the auto-logout issue is fixed
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

def test_token_settings():
    """Test that JWT token settings are configured correctly."""
    print("=== JWT Token Settings ===")
    print(f"ACCESS_TOKEN_LIFETIME: {settings.ACCESS_TOKEN_LIFETIME}")
    print(f"REFRESH_TOKEN_LIFETIME: {settings.REFRESH_TOKEN_LIFETIME}")
    print(f"DEBUG: {settings.DEBUG}")
    print()

def test_token_creation():
    """Test token creation with custom claims."""
    print("=== Token Creation Test ===")
    
    # Get or create a test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        print("Creating test user...")
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    # Create tokens
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    
    print(f"User: {user.username}")
    print(f"Access token expires at: {datetime.fromtimestamp(access['exp'])}")
    print(f"Refresh token created")
    print()
    
    return str(access), str(refresh)

def test_api_endpoints():
    """Test API endpoints for token functionality."""
    print("=== API Endpoints Test ===")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test token obtain endpoint
    try:
        response = requests.post(f"{base_url}/api/token/", {
            'username': 'testuser',
            'password': 'testpass123'
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Token obtain endpoint working")
            print(f"  Access token expires at: {data.get('access_expires_at')}")
            print(f"  Refresh token expires at: {data.get('refresh_expires_at')}")
            print(f"  User info included: {'user' in data}")
            
            # Test token refresh
            refresh_response = requests.post(f"{base_url}/api/token/refresh/", {
                'refresh': data['refresh']
            }, timeout=5)
            
            if refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                print("✓ Token refresh endpoint working")
                print(f"  New access token expires at: {refresh_data.get('access_expires_at')}")
            else:
                print("✗ Token refresh endpoint failed")
                print(f"  Status: {refresh_response.status_code}")
                
        else:
            print("✗ Token obtain endpoint failed")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server")
        print("  Make sure the Django development server is running")
    except Exception as e:
        print(f"✗ Error testing API endpoints: {e}")
    
    print()

def test_middleware_headers():
    """Test that middleware adds the correct headers."""
    print("=== Middleware Headers Test ===")
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        # First get a token
        token_response = requests.post(f"{base_url}/api/token/", {
            'username': 'testuser',
            'password': 'testpass123'
        }, timeout=5)
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data['access']
            
            # Make an authenticated request
            headers = {'Authorization': f'Bearer {access_token}'}
            api_response = requests.get(f"{base_url}/api/users/", headers=headers, timeout=5)
            
            print("Response headers:")
            for header, value in api_response.headers.items():
                if header.startswith('X-'):
                    print(f"  {header}: {value}")
                    
            if 'X-Access-Token-Lifetime' in api_response.headers:
                print("✓ Token lifetime headers present")
            else:
                print("✗ Token lifetime headers missing")
                
        else:
            print("✗ Could not obtain token for testing")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server")
    except Exception as e:
        print(f"✗ Error testing middleware headers: {e}")
    
    print()

def main():
    """Run all tests."""
    print("JWT Token Refresh Test Suite")
    print("=" * 40)
    print()
    
    test_token_settings()
    test_token_creation()
    test_api_endpoints()
    test_middleware_headers()
    
    print("=== Summary ===")
    print("The auto-logout issue should be resolved with these improvements:")
    print(f"1. Extended token lifetimes: {settings.ACCESS_TOKEN_LIFETIME} (access), {settings.REFRESH_TOKEN_LIFETIME} (refresh)")
    print("2. Custom JWT views provide expiration information")
    print("3. Middleware warns when tokens are about to expire")
    print("4. Frontend should implement automatic token refresh")
    print()
    print("Next steps for frontend:")
    print("- Check for X-Token-Refresh-Warning header in API responses")
    print("- Automatically refresh tokens when warning is received")
    print("- Store token expiration times and refresh proactively")

if __name__ == "__main__":
    main()
