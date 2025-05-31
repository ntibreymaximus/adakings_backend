from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('items/', views.MenuItemListView.as_view(), {'item_type': 'regular'}, name='item_list'),
    path('extras/', views.MenuItemListView.as_view(), {'item_type': 'extra'}, name='extra_list'),
    path('item/<int:item_id>/toggle-availability/', views.toggle_menu_item_availability, name='toggle_availability'),
    path('', views.MenuItemListView.as_view(), {'item_type': 'regular'}, name='menu_home'), # Keep this last as a general fallback for /menu/
]
