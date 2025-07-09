from django.apps import AppConfig


class WebsocketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.websockets'
    verbose_name = 'WebSockets'
    
    def ready(self):
        # Import signal handlers
        try:
            from . import signals
        except ImportError:
            pass
