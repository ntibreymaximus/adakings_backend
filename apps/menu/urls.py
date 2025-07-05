from django.urls import path
from .views import (
    MenuItemListCreateAPIView,
    MenuItemRetrieveUpdateDestroyAPIView,
    toggle_menu_item_availability_api
)

app_name = 'menu_api'

urlpatterns = [
    # Root menu endpoint - redirects to items
    path('', MenuItemListCreateAPIView.as_view(), name='menu-root'),
    path('items/', MenuItemListCreateAPIView.as_view(), name='menuitem-list-create'),
    path('items/<int:pk>/', MenuItemRetrieveUpdateDestroyAPIView.as_view(), name='menuitem-detail'),
    path('items/<int:pk>/toggle-availability/', toggle_menu_item_availability_api, name='menuitem-toggle-availability'),
]

