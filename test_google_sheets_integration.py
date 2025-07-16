#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from datetime import datetime
from apps.google_sheets.google_client import get_google_sheets_client

def test_google_sheets():
    print("Testing Google Sheets Integration...")
    print("-" * 50)
    
    try:
        # Get the client
        client = get_google_sheets_client()
        print("✓ Successfully initialized Google Sheets client")
        
        # Check if we're using daily spreadsheets
        print(f"✓ Daily spreadsheets mode: {client.use_daily_spreadsheets}")
        
        # Try to get or create today's sheet
        print(f"\nAttempting to create/access sheet for: {datetime.now().strftime('%d-%m-%Y')}")
        worksheet = client.get_or_create_daily_sheet()
        print("✓ Successfully created/accessed daily sheet")
        
        # Get the spreadsheet URL
        sheet_url = client.get_daily_sheet_url()
        print(f"\n✓ Today's sheet URL: {sheet_url}")
        
        # Test adding a sample order
        test_order_data = {
            'order_number': 'TEST-001',
            'time': datetime.now().strftime('%H:%M:%S'),
            'customer_phone': '+233244123456',
            'delivery_type': 'Pickup',
            'delivery_location': 'Walk-in',
            'items': '1x Test Item @ 10.00',
            'subtotal': 10.00,
            'delivery_fee': 0.00,
            'total_price': 10.00,
            'payment_status': 'UNPAID',
            'order_status': 'Pending',
            'notes': 'Integration test order',
            'created_by': 'System Test'
        }
        
        print("\nTesting order addition...")
        success = client.add_order_to_sheet(test_order_data)
        if success:
            print("✓ Successfully added test order to sheet")
        else:
            print("✗ Failed to add test order")
        
        print("\n" + "=" * 50)
        print("Google Sheets integration test completed!")
        print(f"Check your email ({os.getenv('GOOGLE_SHEETS_SHARE_EMAIL')}) for the shared spreadsheet.")
        print(f"Direct link: {sheet_url}")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_sheets()
