"""
ASGI config for Restaurant Management System (adakings_backend project).

It exposes the ASGI callable as a module-level variable named ``application``.
Supports both HTTP and WebSocket protocols for real-time updates.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.orders import routing as orders_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            orders_routing.websocket_urlpatterns
        )
    ),
})
