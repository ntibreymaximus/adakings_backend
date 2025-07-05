"""
ASGI config for Restaurant Management System (adakings_backend project).

It exposes the ASGI callable as a module-level variable named ``application``.
HTTP-only configuration with WebSocket support removed.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings.settings')

application = get_asgi_application()
