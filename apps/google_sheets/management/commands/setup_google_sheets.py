import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up Google Sheets integration by creating necessary configuration files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--credentials-path',
            type=str,
            help='Path to Google service account credentials JSON file',
        )
        parser.add_argument(
            '--spreadsheet-id',
            type=str,
            help='ID of existing Google Spreadsheet to use (optional)',
        )
        parser.add_argument(
            '--share-email',
            type=str,
            help='Email address to share the spreadsheet with',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up Google Sheets integration...'))
        
        # Create credentials directory
        creds_dir = os.path.join(settings.BASE_DIR, 'credentials')
        os.makedirs(creds_dir, exist_ok=True)
        
        # Handle credentials
        if options['credentials_path']:
            with open(options['credentials_path'], 'r') as f:
                credentials = json.load(f)
            
            # Save to project
            creds_file = os.path.join(creds_dir, 'google-sheets-credentials.json')
            with open(creds_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Saved credentials to {creds_file}'))
        
        # Create .env.google_sheets file
        env_file = os.path.join(settings.BASE_DIR, '.env.google_sheets')
        env_content = []
        
        if options['spreadsheet_id']:
            env_content.append(f"GOOGLE_SHEETS_SPREADSHEET_ID={options['spreadsheet_id']}")
        
        if options['share_email']:
            env_content.append(f"GOOGLE_SHEETS_SHARE_EMAIL={options['share_email']}")
        
        env_content.append("GOOGLE_SHEETS_SYNC_ENABLED=True")
        
        with open(env_file, 'w') as f:
            f.write('\n'.join(env_content))
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {env_file}'))
        
        # Instructions
        self.stdout.write('\n' + self.style.WARNING('Next steps:'))
        self.stdout.write('1. Add the following to your settings.py:')
        self.stdout.write(self.style.SQL("""
# Google Sheets Configuration
GOOGLE_SHEETS_SYNC_ENABLED = env.bool('GOOGLE_SHEETS_SYNC_ENABLED', default=False)
GOOGLE_SHEETS_SPREADSHEET_ID = env.str('GOOGLE_SHEETS_SPREADSHEET_ID', default='')
GOOGLE_SHEETS_SHARE_EMAIL = env.str('GOOGLE_SHEETS_SHARE_EMAIL', default='')
"""))
        
        self.stdout.write('\n2. Add "apps.google_sheets" to INSTALLED_APPS')
        
        self.stdout.write('\n3. Load environment variables from .env.google_sheets')
        
        self.stdout.write('\n4. Install required packages:')
        self.stdout.write(self.style.SQL('pip install google-api-python-client gspread gspread-formatting'))
        
        self.stdout.write('\n' + self.style.SUCCESS('Setup complete!'))
