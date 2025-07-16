import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
from gspread_formatting import *

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GoogleSheetsClientShared:
    """
    Modified Google Sheets client that creates spreadsheets in a shared folder
    owned by a personal Google account instead of the service account.
    """
    
    def __init__(self):
        self.client = None
        self.service = None
        self.drive_service = None
        self.shared_folder_id = None
        self.use_daily_spreadsheets = os.getenv('GOOGLE_SHEETS_DAILY_SPREADSHEETS', 'True').lower() == 'true'
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Sheets client with credentials."""
        try:
            # Get credentials from settings or environment
            credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
            if not credentials_json:
                credentials_path = os.path.join(
                    settings.BASE_DIR, 
                    'credentials', 
                    'google-sheets-credentials.json'
                )
                if os.path.exists(credentials_path):
                    with open(credentials_path, 'r') as f:
                        credentials_json = f.read()
                else:
                    logger.error("Google Sheets credentials not found")
                    return
            
            # Parse credentials
            if isinstance(credentials_json, str):
                credentials_info = json.loads(credentials_json)
            else:
                credentials_info = credentials_json
            
            # Create credentials
            credentials = Credentials.from_service_account_info(
                credentials_info,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            
            # Initialize clients
            self.client = gspread.authorize(credentials)
            self.service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            
            # Get or create shared folder
            self._setup_shared_folder()
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    def _setup_shared_folder(self):
        """
        Setup a shared folder in the user's Google Drive.
        The folder will be created by the service account and shared with the user.
        """
        share_email = os.getenv('GOOGLE_SHEETS_SHARE_EMAIL')
        if not share_email:
            logger.warning("No share email configured")
            return
        
        folder_name = "Adakings Sales Sheets"
        
        try:
            # Search for existing folder shared with the user
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                self.shared_folder_id = folders[0]['id']
                logger.info(f"Using existing shared folder: {self.shared_folder_id}")
            else:
                # Create new folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                self.shared_folder_id = folder.get('id')
                
                # Share folder with user
                permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': share_email
                }
                
                self.drive_service.permissions().create(
                    fileId=self.shared_folder_id,
                    body=permission,
                    transferOwnership=False
                ).execute()
                
                logger.info(f"Created and shared folder: {self.shared_folder_id}")
                
        except Exception as e:
            logger.error(f"Failed to setup shared folder: {e}")
            # Continue without folder (files will be in root)
    
    def _create_spreadsheet_in_folder(self, name: str) -> gspread.Spreadsheet:
        """Create a spreadsheet in the shared folder."""
        try:
            # Create spreadsheet
            spreadsheet = self.client.create(name)
            
            # Move to shared folder if available
            if self.shared_folder_id:
                # Get current parents
                file = self.drive_service.files().get(
                    fileId=spreadsheet.id,
                    fields='parents'
                ).execute()
                
                previous_parents = ",".join(file.get('parents', []))
                
                # Move to shared folder
                self.drive_service.files().update(
                    fileId=spreadsheet.id,
                    addParents=self.shared_folder_id,
                    removeParents=previous_parents,
                    fields='id, parents'
                ).execute()
            
            # Share with user
            share_email = os.getenv('GOOGLE_SHEETS_SHARE_EMAIL')
            if share_email:
                spreadsheet.share(share_email, perm_type='user', role='writer')
            
            return spreadsheet
            
        except Exception as e:
            logger.error(f"Failed to create spreadsheet in folder: {e}")
            raise
    
    def _get_or_create_daily_spreadsheet(self, date: datetime) -> gspread.Spreadsheet:
        """Get or create a spreadsheet for the specified date."""
        sheet_date = date.strftime("%d-%m-%Y")
        cache_key = f"google_sheets_daily_{sheet_date}"
        
        # Check cache first
        cached_id = cache.get(cache_key)
        if cached_id:
            try:
                spreadsheet = self.client.open_by_key(cached_id)
                logger.info(f"Found cached daily spreadsheet: {sheet_date}")
                return spreadsheet
            except:
                cache.delete(cache_key)
        
        try:
            spreadsheet_name = f"Adakings Sales Sheet {sheet_date}"
            
            # Search in shared folder
            if self.shared_folder_id:
                query = f"name='{spreadsheet_name}' and '{self.shared_folder_id}' in parents and trashed=false"
            else:
                query = f"name='{spreadsheet_name}' and trashed=false"
            
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                # Found existing spreadsheet
                spreadsheet = self.client.open_by_key(files[0]['id'])
                cache.set(cache_key, files[0]['id'], 86400)
                logger.info(f"Found existing daily spreadsheet: {sheet_date}")
                return spreadsheet
            
            # Create new spreadsheet
            spreadsheet = self._create_spreadsheet_in_folder(spreadsheet_name)
            
            # Set up the first worksheet
            worksheet = spreadsheet.sheet1
            worksheet.update_title('Orders')
            self._setup_worksheet_headers(worksheet)
            
            # Cache the ID
            cache.set(cache_key, spreadsheet.id, 86400)
            
            logger.info(f"Created new daily spreadsheet: {spreadsheet.id} for {sheet_date}")
            return spreadsheet
            
        except Exception as e:
            logger.error(f"Failed to get or create daily spreadsheet: {e}")
            raise
    
    def get_or_create_daily_sheet(self, date: Optional[datetime] = None) -> gspread.Worksheet:
        """Get or create a worksheet for the specified date."""
        if not date:
            date = datetime.now()
        
        if self.use_daily_spreadsheets:
            spreadsheet = self._get_or_create_daily_spreadsheet(date)
            return spreadsheet.sheet1
        else:
            # Single spreadsheet mode
            if not hasattr(self, 'master_spreadsheet_id'):
                # Create master spreadsheet in shared folder
                spreadsheet = self._create_spreadsheet_in_folder('Adakings Orders Management')
                self.master_spreadsheet_id = spreadsheet.id
            else:
                spreadsheet = self.client.open_by_key(self.master_spreadsheet_id)
            
            sheet_name = date.strftime("%Y-%m-%d")
            
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                logger.info(f"Found existing worksheet: {sheet_name}")
                return worksheet
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=20
                )
                self._setup_worksheet_headers(worksheet)
                logger.info(f"Created new worksheet: {sheet_name}")
                return worksheet
    
    def _setup_worksheet_headers(self, worksheet: gspread.Worksheet):
        """Set up the headers for a new worksheet."""
        headers = [
            'Order Number',
            'Time',
            'Customer Phone',
            'Delivery Type',
            'Delivery Location',
            'Items',
            'Subtotal',
            'Delivery Fee',
            'Total Price',
            'Payment Status',
            'Order Status',
            'Notes',
            'Created By',
            'Last Updated'
        ]
        
        worksheet.update('A1:N1', [headers])
        
        fmt = CellFormat(
            backgroundColor=Color(0.2, 0.3, 0.6),
            textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
            horizontalAlignment='CENTER'
        )
        format_cell_range(worksheet, 'A1:N1', fmt)
        
        set_frozen(worksheet, rows=1)
        
        spreadsheet_id = worksheet.spreadsheet.id
        
        requests = [{
            'updateDimensionProperties': {
                'range': {
                    'sheetId': worksheet.id,
                    'dimension': 'COLUMNS',
                    'startIndex': i,
                    'endIndex': i + 1
                },
                'properties': {
                    'pixelSize': width
                },
                'fields': 'pixelSize'
            }
        } for i, width in enumerate([
            120, 80, 120, 100, 150, 300, 100, 100, 100, 120, 100, 200, 120, 150
        ])]
        
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
    
    # ... (rest of the methods remain the same as the original)
    
    def add_order_to_sheet(self, order_data: Dict[str, Any]) -> bool:
        """Add an order to today's sheet."""
        try:
            worksheet = self.get_or_create_daily_sheet()
            
            row_data = [
                order_data.get('order_number', ''),
                order_data.get('time', datetime.now().strftime('%H:%M:%S')),
                order_data.get('customer_phone', ''),
                order_data.get('delivery_type', ''),
                order_data.get('delivery_location', ''),
                order_data.get('items', ''),
                order_data.get('subtotal', 0),
                order_data.get('delivery_fee', 0),
                order_data.get('total_price', 0),
                order_data.get('payment_status', ''),
                order_data.get('order_status', ''),
                order_data.get('notes', ''),
                order_data.get('created_by', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            worksheet.append_row(row_data)
            
            logger.info(f"Added order {order_data.get('order_number')} to sheet")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add order to sheet: {e}")
            return False


# Singleton instance
_google_sheets_client_shared = None


def get_google_sheets_client_shared():
    """Get or create the singleton GoogleSheetsClientShared instance."""
    global _google_sheets_client_shared
    if _google_sheets_client_shared is None:
        _google_sheets_client_shared = GoogleSheetsClientShared()
    return _google_sheets_client_shared
