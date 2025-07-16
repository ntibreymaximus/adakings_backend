#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')
django.setup()

from datetime import datetime, timedelta
from apps.google_sheets.google_client import get_google_sheets_client

def cleanup_google_drive():
    print("Google Drive Cleanup Tool")
    print("=" * 50)
    
    try:
        client = get_google_sheets_client()
        print("✓ Connected to Google Drive")
        
        # List all spreadsheets
        print("\nFetching spreadsheet list...")
        spreadsheet_list = client.client.list_spreadsheet_files()
        
        print(f"\nFound {len(spreadsheet_list)} spreadsheets in the service account's Drive")
        
        # Sort by creation date (oldest first)
        for sheet in spreadsheet_list[:10]:  # Show first 10
            print(f"- {sheet['name']} (ID: {sheet['id']})")
        
        if len(spreadsheet_list) > 10:
            print(f"... and {len(spreadsheet_list) - 10} more")
        
        # Option to delete old spreadsheets
        print("\n" + "-" * 50)
        print("Options:")
        print("1. Delete all spreadsheets")
        print("2. Delete spreadsheets older than 7 days")
        print("3. Delete specific spreadsheets by pattern")
        print("4. View drive usage")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            confirm = input("Are you sure you want to delete ALL spreadsheets? (yes/no): ")
            if confirm.lower() == 'yes':
                deleted_count = 0
                for sheet in spreadsheet_list:
                    try:
                        client.client.del_spreadsheet(sheet['id'])
                        print(f"Deleted: {sheet['name']}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"Failed to delete {sheet['name']}: {e}")
                print(f"\n✓ Deleted {deleted_count} spreadsheets")
        
        elif choice == "2":
            # This would require checking creation dates
            print("Note: Date-based deletion requires additional API calls")
            print("For now, showing all sheets. You can manually identify old ones.")
            
        elif choice == "3":
            pattern = input("Enter pattern to match (e.g., 'Adakings Sales Sheet'): ")
            matches = [s for s in spreadsheet_list if pattern in s['name']]
            print(f"\nFound {len(matches)} matching spreadsheets:")
            for sheet in matches[:5]:
                print(f"- {sheet['name']}")
            
            if matches:
                confirm = input(f"\nDelete all {len(matches)} matching spreadsheets? (yes/no): ")
                if confirm.lower() == 'yes':
                    deleted_count = 0
                    for sheet in matches:
                        try:
                            client.client.del_spreadsheet(sheet['id'])
                            print(f"Deleted: {sheet['name']}")
                            deleted_count += 1
                        except Exception as e:
                            print(f"Failed to delete {sheet['name']}: {e}")
                    print(f"\n✓ Deleted {deleted_count} spreadsheets")
        
        elif choice == "4":
            print("\nDrive Usage Information:")
            print(f"Total spreadsheets: {len(spreadsheet_list)}")
            print("\nNote: Google provides 15GB free storage per account")
            print("Service accounts share this limit")
            
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_google_drive()
