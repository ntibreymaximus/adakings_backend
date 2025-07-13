#!/usr/bin/env python
"""
Quick test to check API with manual token.
Run this after you get a token from your frontend login.
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = input("Please enter your JWT token (from browser login): ").strip()

# Test orders endpoint
print("\nTesting /api/orders/ with provided token...")
headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

response = requests.get(f"{BASE_URL}/api/orders/", headers=headers)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("Success! API is working correctly.")
    print(f"Response has {len(data)} orders" if isinstance(data, list) else f"Response: {json.dumps(data, indent=2)[:500]}...")
elif response.status_code == 401:
    print("Authentication failed. Token may be invalid or expired.")
    print(f"Response: {response.text}")
elif response.status_code == 400:
    print("Bad Request - there's an issue with the request format.")
    print(f"Response: {response.text}")
else:
    print(f"Unexpected response: {response.text}")

# Also test without token to confirm the difference
print("\n\nTesting without token (should get 401)...")
response = requests.get(f"{BASE_URL}/api/orders/")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text[:200]}...")
