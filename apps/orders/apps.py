from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = 'apps.orders'
    verbose_name = 'Order Management'
    
    def ready(self):
        """
        Import any signals here to ensure they're registered when the app is ready.
        """
        # Import signals if needed
        # from . import signals
