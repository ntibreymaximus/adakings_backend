"""
ASGI config for Restaurant Management System (adakings_backend project).

It exposes the ASGI callable as a module-level variable named ``application``.
Includes WebSocket support for real-time communication.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')

# Initialize Django ASGI application early to ensure the AppRegistry is populated
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

# Import channels components after Django is initialized
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.websockets.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
