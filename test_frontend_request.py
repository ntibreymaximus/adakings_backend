#!/usr/bin/env python
"""
Simulate frontend requests to diagnose the 400 error
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("="*60)
print("SIMULATING FRONTEND REQUESTS")
print("="*60)

# Test 1: Basic GET without auth (like a browser would do)
print("\n1. Testing GET /api/orders/ without auth:")
response = requests.get(f"{BASE_URL}/api/orders/")
print(f"   Status: {response.status_code}")
print(f"   Headers: {dict(response.headers)}")
print(f"   Body: {response.text[:200]}")

# Test 2: GET with wrong auth header format
print("\n2. Testing GET /api/orders/ with malformed auth header:")
headers = {'Authorization': 'invalid-token'}
response = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
print(f"   Status: {response.status_code}")
print(f"   Body: {response.text[:200]}")

# Test 3: OPTIONS request (CORS preflight)
print("\n3. Testing OPTIONS /api/orders/ (CORS preflight):")
headers = {
    'Origin': 'http://localhost:3000',
    'Access-Control-Request-Method': 'GET',
    'Access-Control-Request-Headers': 'authorization,content-type'
}
response = requests.options(f"{BASE_URL}/api/orders/", headers=headers)
print(f"   Status: {response.status_code}")
print(f"   CORS Headers:")
for header, value in response.headers.items():
    if 'access-control' in header.lower() or 'vary' in header.lower():
        print(f"     {header}: {value}")

# Test 4: Check if server is responding correctly
print("\n4. Testing server root:")
response = requests.get(BASE_URL)
print(f"   Status: {response.status_code}")

# Test 5: Check API schema endpoint
print("\n5. Testing API schema endpoint:")
response = requests.get(f"{BASE_URL}/api/schema/")
print(f"   Status: {response.status_code}")

# Test 6: Test with credentials (cookies)
print("\n6. Testing with credentials flag:")
session = requests.Session()
response = session.get(f"{BASE_URL}/api/orders/", 
                      headers={'Origin': 'http://localhost:3000'})
print(f"   Status: {response.status_code}")
print(f"   Cookies: {session.cookies.get_dict()}")

print("\n" + "="*60)
print("DIAGNOSIS:")
print("="*60)
print("\nIf you're getting 400 errors, it might be because:")
print("1. The frontend is sending malformed requests")
print("2. The request body is invalid (for POST requests)")
print("3. There's a middleware intercepting the request")
print("4. The frontend URL path is incorrect")
print("\nCheck your browser's Network tab for the exact request being sent.")
