from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order URLs
    path('', views.OrderListView.as_view(), name='order_list'),
    path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<str:order_number>/update/', views.OrderUpdateView.as_view(), name='order_update'),
    path('<str:order_number>/status/', views.OrderStatusUpdateView.as_view(), name='order_status_update'),
    path('<str:order_number>/items_json/', views.get_order_items_json, name='order_items_json'),
    path('<str:order_number>/ajax_update_status/', views.ajax_update_order_status, name='ajax_order_status_update'),
]

