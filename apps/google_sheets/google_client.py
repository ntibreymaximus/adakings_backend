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


class GoogleSheetsClient:
    """
    Manages Google Sheets operations for order synchronization.
    Supports both single spreadsheet with daily tabs and daily spreadsheets.
    """
    
    def __init__(self):
        self.client = None
        self.service = None
        self.spreadsheet_id = None
        self.use_daily_spreadsheets = os.getenv('GOOGLE_SHEETS_DAILY_SPREADSHEETS', 'False').lower() == 'true'
        self._daily_spreadsheets_cache = {}  # Cache for daily spreadsheet IDs
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
            
            # Get or set the master spreadsheet ID (only used if not using daily spreadsheets)
            if not self.use_daily_spreadsheets:
                self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
                if not self.spreadsheet_id:
                    # Create a master spreadsheet if it doesn't exist
                    self.spreadsheet_id = self._create_master_spreadsheet()
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    def _create_master_spreadsheet(self) -> str:
        """Create the master spreadsheet for orders."""
        try:
            spreadsheet = self.client.create('Adakings Orders Management')
            
            # Share with specific email if configured
            share_email = os.getenv('GOOGLE_SHEETS_SHARE_EMAIL')
            if share_email:
                spreadsheet.share(share_email, perm_type='user', role='writer')
            
            logger.info(f"Created master spreadsheet: {spreadsheet.id}")
            return spreadsheet.id
            
        except Exception as e:
            logger.error(f"Failed to create master spreadsheet: {e}")
            raise
    
    def _get_or_create_daily_spreadsheet(self, date: datetime) -> gspread.Spreadsheet:
        """
        Get or create a spreadsheet for the specified date.
        This creates a new spreadsheet for each day.
        """
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
                # Cached ID is invalid, continue to create/search
                cache.delete(cache_key)
        
        try:
            # Try to find existing spreadsheet by name
            spreadsheet_list = self.client.list_spreadsheet_files()
            spreadsheet_name = f"Adakings Sales Sheet {sheet_date}"
            
            for sheet in spreadsheet_list:
                if sheet['name'] == spreadsheet_name:
                    spreadsheet = self.client.open_by_key(sheet['id'])
                    # Cache the ID
                    cache.set(cache_key, sheet['id'], 86400)  # Cache for 24 hours
                    logger.info(f"Found existing daily spreadsheet: {sheet_date}")
                    return spreadsheet
            
            # Create new spreadsheet for the day
            spreadsheet = self.client.create(spreadsheet_name)
            
            # Share with specific email if configured
            share_email = os.getenv('GOOGLE_SHEETS_SHARE_EMAIL')
            if share_email:
                spreadsheet.share(share_email, perm_type='user', role='writer')
            
            # Set up the first worksheet
            worksheet = spreadsheet.sheet1
            worksheet.update_title('Orders')
            self._setup_worksheet_headers(worksheet)
            
            # Cache the ID
            cache.set(cache_key, spreadsheet.id, 86400)  # Cache for 24 hours
            
            logger.info(f"Created new daily spreadsheet: {spreadsheet.id} for {sheet_date}")
            return spreadsheet
            
        except Exception as e:
            logger.error(f"Failed to get or create daily spreadsheet: {e}")
            raise
    
    def get_or_create_daily_sheet(self, date: Optional[datetime] = None) -> gspread.Worksheet:
        """
        Get or create a worksheet for the specified date.
        
        Args:
            date: The date for the worksheet. Defaults to today.
            
        Returns:
            The worksheet object for the specified date.
        """
        if not date:
            date = datetime.now()
        
        sheet_name = date.strftime("%Y-%m-%d")
        
        try:
            if self.use_daily_spreadsheets:
                # Get or create daily spreadsheet
                spreadsheet = self._get_or_create_daily_spreadsheet(date)
                # Return the first (and only) worksheet
                return spreadsheet.sheet1
            else:
                # Use single spreadsheet with daily tabs
                spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                
                # Try to get existing worksheet
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    logger.info(f"Found existing worksheet: {sheet_name}")
                    return worksheet
                except gspread.WorksheetNotFound:
                    # Create new worksheet
                    worksheet = spreadsheet.add_worksheet(
                        title=sheet_name,
                        rows=1000,
                        cols=20
                    )
                    
                    # Set up headers
                    self._setup_worksheet_headers(worksheet)
                    
                    logger.info(f"Created new worksheet: {sheet_name}")
                    return worksheet
                
        except Exception as e:
            logger.error(f"Failed to get or create daily sheet: {e}")
            raise
    
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
        
        # Update headers
        worksheet.update('A1:N1', [headers])
        
        # Format headers
        fmt = CellFormat(
            backgroundColor=Color(0.2, 0.3, 0.6),
            textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
            horizontalAlignment='CENTER'
        )
        format_cell_range(worksheet, 'A1:N1', fmt)
        
        # Freeze header row
        set_frozen(worksheet, rows=1)
        
        # Get the spreadsheet ID for this worksheet
        spreadsheet_id = worksheet.spreadsheet.id
        
        # Set column widths
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
    
    def add_order_to_sheet(self, order_data: Dict[str, Any]) -> bool:
        """
        Add an order to today's sheet.
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get today's worksheet
            worksheet = self.get_or_create_daily_sheet()
            
            # Prepare row data
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
            
            # Append row
            worksheet.append_row(row_data)
            
            # Apply conditional formatting for payment status
            self._apply_payment_status_formatting(worksheet)
            
            logger.info(f"Added order {order_data.get('order_number')} to sheet")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add order to sheet: {e}")
            return False
    
    def update_order_in_sheet(self, order_number: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing order in today's sheet.
        
        Args:
            order_number: The order number to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self.get_or_create_daily_sheet()
            
            # Find the row with the order number
            cell = worksheet.find(order_number)
            if not cell:
                logger.warning(f"Order {order_number} not found in sheet")
                return False
            
            row_number = cell.row
            
            # Map update fields to column indices
            column_map = {
                'customer_phone': 3,
                'delivery_type': 4,
                'delivery_location': 5,
                'items': 6,
                'subtotal': 7,
                'delivery_fee': 8,
                'total_price': 9,
                'payment_status': 10,
                'order_status': 11,
                'notes': 12,
            }
            
            # Prepare batch update
            updates_list = []
            for field, value in updates.items():
                if field in column_map:
                    col = column_map[field]
                    cell_address = gspread.utils.rowcol_to_a1(row_number, col)
                    updates_list.append({
                        'range': cell_address,
                        'values': [[value]]
                    })
            
            # Always update last updated timestamp
            updates_list.append({
                'range': gspread.utils.rowcol_to_a1(row_number, 14),
                'values': [[datetime.now().strftime('%Y-%m-%d %H:%M:%S')]]
            })
            
            # Batch update
            worksheet.batch_update(updates_list)
            
            logger.info(f"Updated order {order_number} in sheet")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update order in sheet: {e}")
            return False
    
    def _apply_payment_status_formatting(self, worksheet: gspread.Worksheet):
        """Apply conditional formatting to payment status column."""
        try:
            # Get the sheet ID and spreadsheet ID
            sheet_id = worksheet.id
            spreadsheet_id = worksheet.spreadsheet.id
            
            # Define conditional formatting rules
            requests = [{
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{
                            'sheetId': sheet_id,
                            'startColumnIndex': 9,
                            'endColumnIndex': 10,
                            'startRowIndex': 1
                        }],
                        'booleanRule': {
                            'condition': {
                                'type': 'TEXT_EQ',
                                'values': [{'userEnteredValue': status}]
                            },
                            'format': {
                                'backgroundColor': color
                            }
                        }
                    },
                    'index': i
                }
            } for i, (status, color) in enumerate([
                ('PAID', {'red': 0.2, 'green': 0.8, 'blue': 0.2}),
                ('PARTIALLY PAID', {'red': 1, 'green': 0.8, 'blue': 0.2}),
                ('UNPAID', {'red': 0.9, 'green': 0.2, 'blue': 0.2}),
                ('PENDING PAYMENT', {'red': 1, 'green': 0.6, 'blue': 0.2}),
                ('REFUNDED', {'red': 0.5, 'green': 0.5, 'blue': 0.5}),
            ])]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        except Exception as e:
            logger.warning(f"Failed to apply conditional formatting: {e}")
    
    def get_spreadsheet_url(self) -> str:
        """Get the URL of the master spreadsheet or today's spreadsheet."""
        if self.use_daily_spreadsheets:
            # Get today's spreadsheet
            spreadsheet = self._get_or_create_daily_spreadsheet(datetime.now())
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
        else:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
    
    def get_daily_sheet_url(self, date: Optional[datetime] = None) -> str:
        """Get the URL of the daily sheet."""
        if not date:
            date = datetime.now()
        
        if self.use_daily_spreadsheets:
            # Get the daily spreadsheet
            spreadsheet = self._get_or_create_daily_spreadsheet(date)
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
        else:
            # Get the specific worksheet in the master spreadsheet
            sheet_name = date.strftime("%Y-%m-%d")
            worksheet = self.get_or_create_daily_sheet(date)
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit#gid={worksheet.id}"


# Singleton instance
_client_instance = None

def get_google_sheets_client() -> GoogleSheetsClient:
    """Get or create the Google Sheets client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = GoogleSheetsClient()
    return _client_instance
