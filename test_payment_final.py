#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

def test_payment_endpoint():
    """Test the payment endpoint with the fixed order"""
    
    # Payment data that should work now
    payment_data = {
        "order_number": "140725-021",
        "amount": 25.00,
        "payment_method": "mobile_money",
        "mobile_number": "0551234567",
        "payment_type": "order"
    }
    
    url = "http://127.0.0.1:8000/api/payments/initiate/"
    
    print("Testing payment endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payment_data, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(
            url,
            json=payment_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! Payment endpoint is working!")
            try:
                response_data = response.json()
                print(f"Response JSON: {json.dumps(response_data, indent=2)}")
            except:
                print("Response is not valid JSON")
        else:
            print(f"❌ FAILED! Status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server. Make sure Django is running on port 8000.")
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out.")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_payment_endpoint()
