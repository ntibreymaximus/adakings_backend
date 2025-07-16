from django.apps import AppConfig


class GoogleSheetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.google_sheets'
    verbose_name = 'Google Sheets Integration'
    
    def ready(self):
        """Import signal handlers when app is ready."""
        try:
            import apps.google_sheets.signals
        except ImportError:
            pass
