from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes as drf_permission_classes # Renamed to avoid clash
from rest_framework.permissions import IsAdminUser, AllowAny
from apps.users.permissions import IsAdminOrFrontdesk
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes # Added import
from django.shortcuts import get_object_or_404 # Added import
from django.db.models import Q # Added import
from rest_framework.response import Response # Added import

from .models import MenuItem # Added import
from .serializers import MenuItemSerializer # Added import

@extend_schema(
    summary="List and Create Menu Items",
    description="Allows authenticated users to list menu items. Allows admin users to create new ones. Supports filtering by item_type, availability, and search term.",
    parameters=[
        OpenApiParameter(name='item_type', description='Filter by item type (regular or extra)', required=False, type=OpenApiTypes.STR),
        OpenApiParameter(name='availability', description='Filter by availability (available or unavailable)', required=False, type=OpenApiTypes.STR),
        OpenApiParameter(name='search', description='Search by item name', required=False, type=OpenApiTypes.STR),
        OpenApiParameter(name='ordering', description='Order by fields (e.g., name, price, -price)', required=False, type=OpenApiTypes.STR),
    ],
    tags=['Menu']
)
class MenuItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        item_type = self.request.query_params.get('item_type')
        availability = self.request.query_params.get('availability')
        search_query = self.request.query_params.get('search')
        ordering = self.request.query_params.get('ordering')

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
        
        return queryset.select_related("created_by")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

@extend_schema(
    summary="Retrieve, Update, or Delete a Menu Item",
    description="Allows admin users to retrieve, update, or delete a specific menu item.",
    tags=['Menu']
)
class MenuItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrFrontdesk]

    def perform_destroy(self, instance):
        # Superadmins can delete anything, admins can delete menu items, frontdesk cannot delete
        if self.request.user.is_superuser:
            # Superadmins have unrestricted access
            instance.delete()
        elif hasattr(self.request.user, 'role') and self.request.user.role == 'admin':
            # Admins can delete menu items
            instance.delete()
        else:
            raise PermissionDenied("Only admin users and superadmins can delete menu items.")

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
    item.is_available = not item.is_available
    item.save()
    serializer = MenuItemSerializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Remove the old MenuItemListView and toggle_menu_item_availability functions
