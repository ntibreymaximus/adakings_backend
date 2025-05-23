from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order URLs
    path('', views.OrderListView.as_view(), name='order_list'),
    path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/update/', views.OrderUpdateView.as_view(), name='order_update'),
    path('<int:pk>/status/', views.OrderStatusUpdateView.as_view(), name='order_status_update'),
]

