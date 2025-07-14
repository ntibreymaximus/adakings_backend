@echo off
echo Starting Delivery Location Sync Service...
echo This will sync delivery locations every 6 hours.
echo Press Ctrl+C to stop the service.
echo.

cd /d "%~dp0"
python manage.py sync_delivery_locations --interval 6

pause
