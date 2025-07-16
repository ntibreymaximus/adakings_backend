# Google Sheets Integration Guide

This guide explains how to set up and use the Google Sheets integration for real-time order synchronization.

## Overview

The Google Sheets integration automatically syncs orders to Google Sheets in real-time:
- Creates a new spreadsheet for each day (configurable)
- Or creates daily tabs in a single spreadsheet
- Adds orders as they are created
- Updates orders when they are modified
- Tracks payment status changes
- Provides color-coded status indicators

## Setup Instructions

### 1. Create Google Cloud Project and Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create a Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the service account details
   - Grant the role "Editor"
   - Click "Done"
5. Create and download credentials:
   - Click on the service account you created
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose "JSON" format
   - Download the JSON file

### 2. Install Required Packages

```bash
pip install google-api-python-client gspread gspread-formatting
```

Or add to your `requirements.txt`:
```
google-api-python-client>=2.0.0
gspread>=5.0.0
gspread-formatting>=1.0.0
```

### 3. Configure Django Settings

Add to your `settings.py`:

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'apps.google_sheets',
]

# Google Sheets Configuration
from dotenv import load_dotenv
load_dotenv('.env.google_sheets')  # Load Google Sheets specific env vars

GOOGLE_SHEETS_SYNC_ENABLED = env.bool('GOOGLE_SHEETS_SYNC_ENABLED', default=False)
GOOGLE_SHEETS_DAILY_SPREADSHEETS = env.bool('GOOGLE_SHEETS_DAILY_SPREADSHEETS', default=True)
GOOGLE_SHEETS_SPREADSHEET_ID = env.str('GOOGLE_SHEETS_SPREADSHEET_ID', default='')
GOOGLE_SHEETS_SHARE_EMAIL = env.str('GOOGLE_SHEETS_SHARE_EMAIL', default='')
```

### 4. Set Up Credentials

Run the setup command:

```bash
python manage.py setup_google_sheets \
    --credentials-path=/path/to/your/service-account-key.json \
    --share-email=maximuslambertntibrey.mln@gmail.com
```

This will:
- Save credentials to `credentials/google-sheets-credentials.json`
- Create `.env.google_sheets` with configuration
- Provide further setup instructions

### 5. Add URL Configuration

In your main `urls.py`, add:

```python
urlpatterns = [
    # ... other patterns
    path('api/google-sheets/', include('apps.google_sheets.urls')),
]
```

### 6. Test the Connection

```bash
# Using curl
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/google-sheets/test-connection/

# Or using the management command
python manage.py test_google_sheets_connection
```

## Usage

### Automatic Synchronization

Once configured, orders will automatically sync to Google Sheets:

1. **New Orders**: When an order is created, it's added to today's sheet
2. **Updates**: Order modifications are reflected in real-time
3. **Payment Status**: Payment changes update the sheet immediately
4. **Status Changes**: Order status updates are synced automatically

### Manual Operations

#### Get Google Sheets URLs
```bash
GET /api/google-sheets/sheets-url/
```

Response:
```json
{
    "master_spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
    "today_sheet_url": "https://docs.google.com/spreadsheets/d/.../edit#gid=...",
    "spreadsheet_id": "1234567890",
    "sync_enabled": true
}
```

#### Sync Single Order
```bash
POST /api/google-sheets/sync/{order_number}/
```

#### Bulk Sync Orders
```bash
POST /api/google-sheets/bulk-sync/?start_date=2024-01-01&end_date=2024-01-31
```

### Sheet Structure

Each daily sheet contains the following columns:

| Column | Description |
|--------|-------------|
| Order Number | Unique order identifier (e.g., 161124-001) |
| Time | Order creation time |
| Customer Phone | Customer's phone number |
| Delivery Type | Pickup or Delivery |
| Delivery Location | Delivery location name |
| Items | Order items with quantities |
| Subtotal | Total before delivery fee |
| Delivery Fee | Delivery charge |
| Total Price | Final order total |
| Payment Status | PAID, UNPAID, PARTIALLY PAID, etc. |
| Order Status | Pending, Accepted, Ready, etc. |
| Notes | Order notes |
| Created By | User who created the order |
| Last Updated | Last modification timestamp |

### Color Coding

Payment statuses are color-coded:
- **PAID**: Green
- **PARTIALLY PAID**: Yellow
- **UNPAID**: Red
- **PENDING PAYMENT**: Orange
- **REFUNDED**: Gray

### Spreadsheet Organization

#### Daily Spreadsheets Mode (GOOGLE_SHEETS_DAILY_SPREADSHEETS=True)
- Creates a new spreadsheet for each day
- Named: "Adakings Sales Sheet DD-MM-YYYY"
- Each spreadsheet contains all orders for that day
- Easier to share specific days with staff
- Better for archiving and backup

#### Single Spreadsheet Mode (GOOGLE_SHEETS_DAILY_SPREADSHEETS=False)
- Uses one master spreadsheet
- Creates a new tab/worksheet for each day
- All data in one place
- Better for overview and reporting
- Requires GOOGLE_SHEETS_SPREADSHEET_ID to be set

## Troubleshooting

### Common Issues

1. **Authentication Error**
   - Verify service account credentials are correct
   - Ensure Google Sheets API is enabled
   - Check file permissions for credentials

2. **Spreadsheet Not Found**
   - Verify GOOGLE_SHEETS_SPREADSHEET_ID is correct
   - Ensure service account has access to the spreadsheet

3. **Sync Not Working**
   - Check GOOGLE_SHEETS_SYNC_ENABLED is True
   - Verify credentials are properly configured
   - Check Django logs for errors

### Debug Mode

Enable debug logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.google_sheets': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Security Considerations

1. **Service Account Credentials**
   - Never commit credentials to version control
   - Store securely with restricted access
   - Use environment variables in production

2. **Spreadsheet Access**
   - Only share with necessary users
   - Use view-only access where possible
   - Regularly audit access permissions

3. **Data Privacy**
   - Be mindful of customer data in sheets
   - Implement appropriate retention policies
   - Consider data anonymization for reports

## Advanced Configuration

### Disable Sync for Specific Operations

```python
# In your code
order._skip_sheets_sync = True
order.save()  # This won't trigger Google Sheets sync
```

### Custom Sheet Names

Modify `get_or_create_daily_sheet` in `google_client.py`:

```python
# Example: Use month-year format
sheet_name = date.strftime("%B-%Y")  # January-2024
```

### Additional Columns

Add custom columns by modifying:
1. `_setup_worksheet_headers` in `google_client.py`
2. `prepare_order_data` in `signals.py`
3. Column mapping in `update_order_in_sheet`

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/google-sheets/sheets-url/` | Get spreadsheet URLs |
| GET | `/api/google-sheets/test-connection/` | Test connection |
| POST | `/api/google-sheets/sync/{order_number}/` | Sync specific order |
| POST | `/api/google-sheets/bulk-sync/` | Bulk sync orders |

### Permissions

All endpoints require authentication:
- `sheets-url`: Any authenticated user
- `test-connection`: Admin or Frontdesk
- `sync/*`: Admin or Frontdesk
- `bulk-sync`: Admin or Frontdesk

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django logs
3. Verify Google Cloud Console settings
4. Contact system administrator
