from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes as drf_permission_classes # Renamed to avoid clash
from rest_framework.permissions import IsAdminUser, AllowAny
from apps.users.permissions import IsAdminOrFrontdesk
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes # Added import
from django.shortcuts import get_object_or_404 # Added import
from django.db.models import Q, Prefetch # Added import
from rest_framework.response import Response # Added import
from django.core.cache import cache
from apps.audit.utils import log_create, log_update, log_delete, log_toggle
import logging


from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.conf import settings
import hashlib


def clear_menu_cache():
    """Clear all menu-related cache entries with backend compatibility."""
    try:
        # Try to use keys() method for Redis cache
        if hasattr(cache, 'keys'):
            cache.delete_many(cache.keys('menu_items_*'))
        else:
            # For LocMemCache and other backends without keys() support
            # Clear specific known cache keys or use cache.clear() for development
            if settings.DEBUG:
                cache.clear()  # Safe to clear all cache in development
            else:
                # In production, we would need to track cache keys manually
                # For now, just skip cache clearing for unsupported backends
                pass
    except Exception as e:
        # Log the error but don't break the application
        print(f"Cache clearing error: {e}")

from .models import MenuItem # Added import
from .serializers import MenuItemSerializer # Added import

@extend_schema(
    summary="List and Create Menu Items",
    description="Allows authenticated users to list menu items. Allows admin users to create new ones. Supports filtering by item_type, availability, and search term.",
    parameters=[
        OpenApiParameter(name='item_type', description='Filter by item type (regular, extra, or bolt)', required=False, type=OpenApiTypes.STR),
        OpenApiParameter(name='availability', description='Filter by availability (available or unavailable)', required=False, type=OpenApiTypes.STR),
        OpenApiParameter(name='search', description='Search by item name', required=False, type=OpenApiTypes.STR),
        OpenApiParameter(name='ordering', description='Order by fields (e.g., name, price, -price)', required=False, type=OpenApiTypes.STR),
    ],
    tags=['Menu']
)
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class MenuItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_cache_key(self):
        """Generate cache key based on query parameters"""
        params = self.request.query_params
        key_parts = [
            'menu_items',
            params.get('item_type', 'all'),
            params.get('availability', 'all'),
            params.get('search', ''),
            params.get('ordering', 'default'),
        ]
        key = '_'.join(str(part) for part in key_parts)
        return hashlib.md5(key.encode()).hexdigest()

    def list(self, request, *args, **kwargs):
        """Override list method to add caching"""
        cache_key = self.get_cache_key()
        
        # Try to get from cache first
        cached_response = cache.get(cache_key)
        if cached_response and not settings.DEBUG:
            # Add cache hit header for debugging
            response = Response(cached_response)
            response['X-Cache'] = 'HIT'
            # Add browser cache headers
            response['Cache-Control'] = 'public, max-age=300'
            response['ETag'] = f'"{cache_key}"'
            return response
        
        # Get fresh data
        response = super().list(request, *args, **kwargs)
        
        # Cache the response data for 5 minutes
        if response.status_code == 200:
            cache.set(cache_key, response.data, 300)
            response['X-Cache'] = 'MISS'
            # Add browser cache headers for fresh responses
            response['Cache-Control'] = 'public, max-age=300'
            response['ETag'] = f'"{cache_key}"'
        
        return response

    def get_queryset(self):
        queryset = super().get_queryset()
        item_type = self.request.query_params.get('item_type')
        availability = self.request.query_params.get('availability')
        search_query = self.request.query_params.get('search')
        ordering = self.request.query_params.get('ordering')

        # Apply filters with optimized queries
        if item_type:
            queryset = queryset.filter(item_type=item_type)
        if availability:
            queryset = queryset.filter(is_available=(availability.lower() == "available"))
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query))
        if ordering:
            queryset = queryset.order_by(*ordering.split(','))
        else:
            queryset = queryset.order_by('item_type', 'name') # Default ordering
        
        # Optimize query with select_related for faster joins
        return queryset.select_related("created_by")

    def perform_create(self, serializer):
        """Clear cache after creating new menu item"""
        instance = serializer.save(created_by=self.request.user)
        # Log menu item creation
        log_create(
            user=self.request.user,
            obj=instance,
            request=self.request,
            extra_data={
                'item_name': instance.name,
                'item_type': instance.item_type,
                'price': str(instance.price),
                'is_available': instance.is_available
            }
        )
        # Clear all menu-related cache entries
        clear_menu_cache()
        return instance

@extend_schema(
    summary="Retrieve, Update, or Delete a Menu Item",
    description="Allows admin users to retrieve, update, or delete a specific menu item.",
    tags=['Menu']
)
class MenuItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.select_related('created_by')  # Optimize queries
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrFrontdesk]

    def perform_update(self, serializer):
        """Clear cache after updating menu item"""
        # Get the changes before saving
        from apps.audit.utils import get_model_changes
        changes = get_model_changes(serializer.instance, serializer.validated_data)
        
        instance = serializer.save()
        
        # Log menu item update
        log_update(
            user=self.request.user,
            obj=instance,
            old_values=changes,
            new_values=serializer.validated_data,
            request=self.request
        )
        
        # Clear all menu-related cache entries
        clear_menu_cache()
        return instance

    def perform_destroy(self, instance):
        # Superadmins can delete anything, admins can delete menu items, frontdesk cannot delete
        if self.request.user.is_superuser:
            # Superadmins have unrestricted access
            # Log deletion before actually deleting
            log_delete(
                user=self.request.user,
                obj=instance,
                request=self.request
            )
            instance.delete()
        elif hasattr(self.request.user, 'role') and self.request.user.role == 'admin':
            # Admins can delete menu items
            # Log deletion before actually deleting
            log_delete(
                user=self.request.user,
                obj=instance,
                request=self.request
            )
            instance.delete()
        else:
            raise PermissionDenied("Only admin users and superadmins can delete menu items.")
        
        # Clear all menu-related cache entries after deletion
        clear_menu_cache()

@extend_schema(
    summary="Toggle Menu Item Availability",
    description="Allows admin or frontdesk users to toggle the availability of a menu item.",
    request=None, # No request body for this PUT action
    responses={200: MenuItemSerializer}, # Returns the updated menu item
    tags=['Menu']
)
@api_view(['PUT'])
@drf_permission_classes([IsAdminOrFrontdesk])
def toggle_menu_item_availability_api(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    old_availability = item.is_available
    item.is_available = not item.is_available
    
    try:
        item.save()
    except Exception as e:
        logging.error(f"Error toggling availability for menu item {pk}: {e}")
        return Response({'detail': 'Error toggling availability.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Log the availability toggle
    log_toggle(
        user=request.user,
        obj=item,
        field_name='is_available',
        old_value=old_availability,
        new_value=item.is_available,
        request=request
    )
    
    # Clear all menu-related cache entries after toggling availability
    clear_menu_cache()
    
    serializer = MenuItemSerializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Remove the old MenuItemListView and toggle_menu_item_availability functions
