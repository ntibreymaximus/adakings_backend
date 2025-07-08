"""
Context processors for Adakings Backend
Adds environment information to all Django templates
"""

import os
from django.conf import settings


def environment_info(request):
    """
    Add environment information to all template contexts.
    This allows templates to show environment tags on backend pages.
    """
    # Determine environment
    is_railway = 'RAILWAY_ENVIRONMENT' in os.environ
    django_env = os.environ.get('DJANGO_ENVIRONMENT', 'local')
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT', '')
    
    # Determine platform
    platform = "Railway" if is_railway else "Local"
    
    # Determine UI tag display logic
    if not is_railway:
        # Local development
        ui_tag = "LOCAL"
        ui_tag_class = "env-tag-local"
        show_tag = True
    elif django_env == 'development' or railway_env == 'dev':
        # Development server on Railway
        ui_tag = "DEV-SERVER"
        ui_tag_class = "env-tag-dev"
        show_tag = True
    else:
        # Production - don't show tag
        ui_tag = None
        ui_tag_class = None
        show_tag = False
    
    # Get version
    version = "1.0.0"
    try:
        with open(os.path.join(settings.BASE_DIR, 'VERSION'), 'r') as f:
            version = f.read().strip()
    except FileNotFoundError:
        pass
    
    return {
        'environment_info': {
            'environment': django_env,
            'platform': platform,
            'debug': settings.DEBUG,
            'version': version,
            'ui_tag': ui_tag,
            'ui_tag_class': ui_tag_class,
            'show_tag': show_tag,
            'is_railway': is_railway,
            'is_local': not is_railway,
        }
    }
