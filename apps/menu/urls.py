from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('items/', views.MenuItemListView.as_view(), name='item_list'),
    path('extras/', views.ExtraListView.as_view(), name='extra_list'),
    path('', views.MenuItemListView.as_view(), name='menu_home'),
]
