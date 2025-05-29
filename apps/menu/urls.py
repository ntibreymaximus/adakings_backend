from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('items/', views.MenuItemListView.as_view(), {'item_type': 'regular'}, name='item_list'),
    path('extras/', views.MenuItemListView.as_view(), {'item_type': 'extra'}, name='extra_list'),
    path('', views.MenuItemListView.as_view(), {'item_type': 'regular'}, name='menu_home'),
]
