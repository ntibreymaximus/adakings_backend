"""
URL configuration for Restaurant Management System (adakings_backend project).

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import environment_info, health_check



# Serializer for api_root response
class APIRootSerializer(serializers.Serializer):
    users = serializers.URLField()
    menu = serializers.URLField() # Added
    orders = serializers.URLField() # Added
    payments = serializers.URLField() # Added
    environment = serializers.URLField()  # Added
    health = serializers.URLField()  # Added
    schema = serializers.URLField()
    docs = serializers.URLField()
    swagger = serializers.URLField()

@extend_schema(responses=APIRootSerializer)
@api_view(['GET'])
@permission_classes([AllowAny]) # Add this line
def api_root(request, format=None):
    return Response({
        'users': reverse('users_api:user-list', request=request, format=format),
        'menu': reverse('menu_api:menuitem-list-create', request=request, format=format), # Added
        'orders': reverse('orders_api:order-list-create', request=request, format=format), # Added
        'payments': reverse('payments_api:payment-list', request=request, format=format), # Added
        'environment': reverse('environment-info', request=request, format=format),  # Added
        'health': reverse('health-check', request=request, format=format),  # Added
        'schema': reverse('schema', request=request, format=format),
        'docs': reverse('redoc', request=request, format=format),
        'swagger': reverse('swagger-ui', request=request, format=format),
    })

urlpatterns = [

    # Menu app API URLs
    path('api/menu/', include('apps.menu.urls')),

    # Orders app API URLs
    path('api/orders/', include('apps.orders.urls')),

    # Payments app API URLs
    path('api/payments/', include('apps.payments.urls')),


    # JWT token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # System endpoints
    path('api/environment/', environment_info, name='environment-info'),
    path('api/health/', health_check, name='health-check'),
    path('health/', health_check, name='health-check-root'),  # For load balancers
    
    # API Root
    path('api/', api_root, name='api-root'),
    path('api/users/', include('apps.users.urls')),

    # DRF Spectacular URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Admin URLs
    path('admin/', admin.site.urls),
    
    # Root URL redirects to admin page
    path('', RedirectView.as_view(url='/admin/', permanent=False), name='home'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Django Debug Toolbar URLs
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
