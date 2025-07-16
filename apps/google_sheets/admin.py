from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.conf import settings
from django.contrib import messages

from .google_client_shared import get_google_sheets_client_shared as get_google_sheets_client


class GoogleSheetsAdmin(admin.ModelAdmin):
    """
    Admin interface for Google Sheets integration settings.
    This is a virtual model admin that doesn't have a database model.
    """
    
    def has_module_permission(self, request):
        """Only show in admin if Google Sheets sync is enabled."""
        return getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', False)
    
    def changelist_view(self, request, extra_context=None):
        """Display Google Sheets integration status and controls."""
        extra_context = extra_context or {}
        
        try:
            client = get_google_sheets_client()
            extra_context.update({
                'sync_enabled': True,
                'spreadsheet_id': client.spreadsheet_id,
                'spreadsheet_url': client.get_spreadsheet_url(),
                'today_sheet_url': client.get_daily_sheet_url(),
                'connection_status': 'Connected',
                'connection_class': 'success',
            })
        except Exception as e:
            extra_context.update({
                'sync_enabled': getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', False),
                'connection_status': f'Error: {str(e)}',
                'connection_class': 'error',
            })
        
        # Add API URLs
        extra_context.update({
            'test_connection_url': reverse('api:google_sheets:test-connection'),
            'sheets_url_api': reverse('api:google_sheets:sheets-url'),
            'bulk_sync_url': reverse('api:google_sheets:bulk-sync'),
        })
        
        return super().changelist_view(request, extra_context=extra_context)


# Create a fake model to register with admin
class GoogleSheetsConfig:
    class Meta:
        app_label = 'google_sheets'
        verbose_name = 'Google Sheets Settings'
        verbose_name_plural = 'Google Sheets Settings'


# Only register if the app is installed
try:
    admin.site.register(GoogleSheetsConfig, GoogleSheetsAdmin)
except:
    pass
