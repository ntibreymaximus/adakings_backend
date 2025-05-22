from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'User Management'

    def ready(self):
        """
        Import signals when the app is ready.
        This ensures that any signal handlers are registered.
        """
        try:
            import apps.users.signals  # noqa
        except ImportError:
            # Handle the case where signals.py doesn't exist yet
            pass
