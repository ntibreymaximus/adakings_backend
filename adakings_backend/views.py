"""
Core views for Adakings Backend API
Provides system and environment information endpoints
"""

import os
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework import serializers


class EnvironmentInfoSerializer(serializers.Serializer):
    """Serializer for environment information response"""
    environment = serializers.CharField(help_text="Current environment (local, development, production)")
    platform = serializers.CharField(help_text="Platform (Railway, Local)")
    debug = serializers.BooleanField(help_text="Debug mode status")
    version = serializers.CharField(help_text="Application version")
    ui_tag = serializers.CharField(help_text="UI tag to display (local, dev-server, none)")
    show_tag = serializers.BooleanField(help_text="Whether to show the environment tag")


@extend_schema(
    summary="Get Environment Information",
    description="Returns environment information for frontend UI display",
    responses={200: EnvironmentInfoSerializer},
    tags=["System"]
)
@api_view(['GET'])
@permission_classes([AllowAny])
def environment_info(request):
    """
    Get current environment information for frontend display.
    
    Returns:
    - environment: Current environment name
    - platform: Platform (Railway/Local)
    - debug: Debug mode status
    - version: Application version
    - ui_tag: Tag to display in frontend
    - show_tag: Whether to show environment tag
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
        ui_tag = "local"
        show_tag = True
    elif django_env == 'development' or railway_env == 'dev':
        # Development server on Railway
        ui_tag = "dev-server"
        show_tag = True
    else:
        # Production - don't show tag
        ui_tag = None
        show_tag = False
    
    # Get version
    version = "1.0.0"
    try:
        with open(os.path.join(settings.BASE_DIR, 'VERSION'), 'r') as f:
            version = f.read().strip()
    except FileNotFoundError:
        pass
    
    return Response({
        'environment': django_env,
        'platform': platform,
        'debug': settings.DEBUG,
        'version': version,
        'ui_tag': ui_tag,
        'show_tag': show_tag
    })


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check response"""
    status = serializers.CharField(help_text="Health status")
    environment = serializers.CharField(help_text="Current environment")
    timestamp = serializers.DateTimeField(help_text="Response timestamp")
    database = serializers.CharField(help_text="Database connection status")


@extend_schema(
    summary="Health Check",
    description="Basic health check endpoint for monitoring",
    responses={200: HealthCheckSerializer},
    tags=["System"]
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint for monitoring and load balancers.
    """
    from django.utils import timezone
    from django.db import connection
    
    # Test database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return Response({
        'status': 'healthy',
        'environment': os.environ.get('DJANGO_ENVIRONMENT', 'local'),
        'timestamp': timezone.now(),
        'database': db_status
    })
