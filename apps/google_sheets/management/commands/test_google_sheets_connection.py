from django.core.management.base import BaseCommand
from django.conf import settings
from apps.google_sheets.google_client_shared import get_google_sheets_client_shared as get_google_sheets_client
from datetime import datetime


class Command(BaseCommand):
    help = 'Test Google Sheets connection and configuration'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Google Sheets connection...\n'))
        
        # Check if sync is enabled
        sync_enabled = getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', False)
        if not sync_enabled:
            self.stdout.write(self.style.ERROR('✗ Google Sheets sync is not enabled'))
            self.stdout.write('  Set GOOGLE_SHEETS_SYNC_ENABLED=True in your settings')
            return
        
        self.stdout.write(self.style.SUCCESS('✓ Google Sheets sync is enabled'))
        
        # Test connection
        try:
            client = get_google_sheets_client()
            self.stdout.write(self.style.SUCCESS('✓ Successfully initialized Google Sheets client'))
            
            # Display client configuration
            self.stdout.write('\nClient Configuration:')
            self.stdout.write(f'  Mode: {"Daily Spreadsheets" if client.use_daily_spreadsheets else "Single Spreadsheet with Daily Tabs"}')
            if hasattr(client, 'shared_folder_id') and client.shared_folder_id:
                self.stdout.write(f'  Shared Folder ID: {client.shared_folder_id}')
            if hasattr(client, 'sharing_email') and client.sharing_email:
                self.stdout.write(f'  Sharing with: {client.sharing_email}')
            
            # Test creating/accessing today's sheet
            self.stdout.write('\n' + self.style.SUCCESS('Testing daily sheet creation...'))
            worksheet = client.get_or_create_daily_sheet()
            self.stdout.write(self.style.SUCCESS(f'✓ Today\'s sheet: {worksheet.title}'))
            
            # Get the spreadsheet for today
            if client.use_daily_spreadsheets:
                today = datetime.now()
                sheet_date = today.strftime("%d-%m-%Y")
                spreadsheet_name = f"Adakings Sales Sheet {sheet_date}"
                self.stdout.write(f'  Spreadsheet: {spreadsheet_name}')
                self.stdout.write(f'  URL: {client.get_spreadsheet_url()}')
            else:
                # Single spreadsheet mode
                spreadsheet = worksheet.spreadsheet
                self.stdout.write(f'  Spreadsheet: {spreadsheet.title}')
                self.stdout.write(f'  Spreadsheet ID: {spreadsheet.id}')
                self.stdout.write(f'  URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}')
                
                # List worksheets in single spreadsheet mode
                worksheets = spreadsheet.worksheets()
                self.stdout.write(f'\n  Found {len(worksheets)} worksheet(s):')
                for ws in worksheets[:5]:  # Show first 5
                    self.stdout.write(f'    - {ws.title}')
                if len(worksheets) > 5:
                    self.stdout.write(f'    ... and {len(worksheets) - 5} more')
            
            # Test permissions
            self.stdout.write('\n' + self.style.SUCCESS('Testing write permissions...'))
            test_row = ['TEST', 'Connection test - this row can be deleted']
            worksheet.append_row(test_row)
            self.stdout.write(self.style.SUCCESS('✓ Successfully wrote test data'))
            
            # Summary
            self.stdout.write('\n' + self.style.SUCCESS('=' * 50))
            self.stdout.write(self.style.SUCCESS('Google Sheets integration is working correctly!'))
            self.stdout.write(self.style.SUCCESS('=' * 50))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Connection failed: {str(e)}'))
            self.stdout.write('\nTroubleshooting steps:')
            self.stdout.write('1. Check that credentials file exists')
            self.stdout.write('2. Verify Google Sheets API and Drive API are enabled in Google Cloud Console')
            self.stdout.write('3. If using shared folder, ensure service account has access')
            self.stdout.write('4. Check environment variables are correctly set')
