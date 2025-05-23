"""
URL configuration for restaurant_frontdesk project.

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
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# Simple redirect view for the root URL to dashboard or login
def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return redirect('users:login')

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    
    # Users app URLs
    path('users/', include('apps.users.urls')),
    
    # Menu app URLs
    path('menu/', include('apps.menu.urls')),
    
    # Orders app URLs
    path('orders/', include('apps.orders.urls')),
    
    # Payments app URLs
    path('payments/', include('apps.payments.urls', namespace='payments')),
    
    # Root URL redirects to dashboard or login page
    path('', home_redirect, name='home'),
    
    # Dashboard redirects (for convenience)
    path('dashboard/', RedirectView.as_view(pattern_name='users:dashboard'), name='dashboard'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
