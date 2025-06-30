from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderListCreateAPIView,
    OrderRetrieveUpdateDestroyAPIView,
    OrderStatusUpdateAPIView,
    DeliveryLocationListAPIView,
    OrderStatusHistoryAPIView,
    next_order_number
)

app_name = 'orders_api'

# No router needed if we are using separate views for now.
# router = DefaultRouter()
# router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    # path('', include(router.urls)),
    path('', OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('next-order-number/', next_order_number, name='next-order-number'),
    path('delivery-locations/', DeliveryLocationListAPIView.as_view(), name='delivery-locations'),
    path('status-history/', OrderStatusHistoryAPIView.as_view(), name='order-status-history'),
    path('<str:order_number>/', OrderRetrieveUpdateDestroyAPIView.as_view(), name='order-detail'),
    path('<str:order_number>/status/', OrderStatusUpdateAPIView.as_view(), name='order-status-update'),
]

