# Google Sheets Integration Setup Instructions

The Google Sheets integration has been successfully installed and configured in your Adakings backend. Follow these steps to enable it:

## Step 1: Create a Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
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

## Step 2: Configure Your Environment

1. Copy the downloaded JSON file to: `credentials/google-sheets-credentials.json`

2. Edit `.env.google_sheets` file:
   ```
   GOOGLE_SHEETS_SYNC_ENABLED=True
   GOOGLE_SHEETS_DAILY_SPREADSHEETS=True  # Creates new spreadsheet for each day
   GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id  # Only needed if DAILY_SPREADSHEETS=False
   GOOGLE_SHEETS_SHARE_EMAIL=maximuslambertntibrey.mln@gmail.com
   ```

   To get the spreadsheet ID:
   - Create a new Google Sheet or use an existing one
   - The URL will be: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the SPREADSHEET_ID part

3. Share the spreadsheet with your service account:
   - Open your Google Sheet
   - Click "Share"
   - Add the service account email (found in the JSON file as "client_email")
   - Give it "Editor" access

## Step 3: Test the Connection

Run the test command:
```bash
python manage.py test_google_sheets_connection
```

## Step 4: Run Your Server

Start your Django server:
```bash
python manage.py runserver
```

## How It Works

Once enabled, the system will:
- Automatically create a new spreadsheet for each day
- Named: "Adakings Sales Sheet DD-MM-YYYY" (e.g., "Adakings Sales Sheet 16-07-2025")
- Add new orders to the sheet in real-time
- Update orders when they are modified
- Track payment status changes
- Use color coding for payment statuses

## API Endpoints

- **Get Sheet URLs**: `GET /api/google-sheets/sheets-url/`
- **Test Connection**: `GET /api/google-sheets/test-connection/`
- **Sync Order**: `POST /api/google-sheets/sync/{order_number}/`
- **Bulk Sync**: `POST /api/google-sheets/bulk-sync/`

## Troubleshooting

If you encounter issues:
1. Check that `GOOGLE_SHEETS_SYNC_ENABLED=True` in `.env.google_sheets`
2. Verify the service account credentials file exists in `credentials/`
3. Ensure the Google Sheets API is enabled in Google Cloud Console
4. Confirm the service account has access to your spreadsheet

For more details, see: `docs/GOOGLE_SHEETS_INTEGRATION.md`
