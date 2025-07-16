#!/usr/bin/env python
import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread

def direct_cleanup():
    print("Direct Google Drive Cleanup")
    print("=" * 50)
    
    try:
        # Load credentials directly
        credentials_path = os.path.join('credentials', 'google-sheets-credentials.json')
        
        if not os.path.exists(credentials_path):
            print("❌ Credentials file not found at:", credentials_path)
            return
            
        with open(credentials_path, 'r') as f:
            credentials_info = json.load(f)
        
        # Create credentials
        credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        
        # Initialize client
        client = gspread.authorize(credentials)
        print("✓ Connected to Google Drive")
        
        # Get service account email
        service_account_email = credentials_info.get('client_email', 'Unknown')
        print(f"Service Account: {service_account_email}")
        
        # List all spreadsheets
        print("\nFetching spreadsheet list...")
        try:
            spreadsheet_list = client.list_spreadsheet_files()
            print(f"\n✓ Found {len(spreadsheet_list)} spreadsheets")
            
            if not spreadsheet_list:
                print("No spreadsheets found to delete.")
                return
                
            # Show first 20
            print("\nSpreadsheets in Drive:")
            for i, sheet in enumerate(spreadsheet_list[:20]):
                print(f"{i+1}. {sheet['name']} (ID: {sheet['id']})")
            
            if len(spreadsheet_list) > 20:
                print(f"... and {len(spreadsheet_list) - 20} more")
            
            # Offer to delete all
            print("\n" + "-" * 50)
            print("⚠️  IMPORTANT: The service account's Drive is FULL!")
            print("You need to delete some spreadsheets to continue.")
            print("-" * 50)
            
            choice = input("\nDelete ALL spreadsheets to free up space? (yes/no): ")
            
            if choice.lower() == 'yes':
                print("\nDeleting spreadsheets...")
                deleted_count = 0
                failed_count = 0
                
                for sheet in spreadsheet_list:
                    try:
                        client.del_spreadsheet(sheet['id'])
                        print(f"✓ Deleted: {sheet['name']}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"✗ Failed to delete {sheet['name']}: {e}")
                        failed_count += 1
                
                print("\n" + "=" * 50)
                print(f"✓ Successfully deleted {deleted_count} spreadsheets")
                if failed_count > 0:
                    print(f"✗ Failed to delete {failed_count} spreadsheets")
                print("\nThe service account's Drive should now have free space!")
                print("You can now run the test again.")
            else:
                print("\nNo spreadsheets deleted. The Drive remains full.")
                print("You won't be able to create new spreadsheets until space is freed.")
                
        except Exception as e:
            print(f"\n✗ Error listing spreadsheets: {e}")
            print("\nThis might mean:")
            print("1. The Drive API is not enabled")
            print("2. The service account doesn't have proper permissions")
            print("3. There's a network issue")
            
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    direct_cleanup()
