from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderListCreateAPIView,
    OrderRetrieveUpdateDestroyAPIView,
    OrderStatusUpdateAPIView,
    DeliveryLocationListAPIView,
    OrderStatusHistoryAPIView,
    next_order_number,
    todays_orders,
    order_options,
    order_stats,
    quick_stats
)
from .views_export_import import (
    export_orders,
    import_orders,
    download_import_template
)

app_name = 'orders_api'

# No router needed if we are using separate views for now.
# router = DefaultRouter()
# router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
# path('', include(router.urls)),
    path('', OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('export/', export_orders, name='order-export'),
    path('import/', import_orders, name='order-import'),
    path('download-template/', download_import_template, name='import-template'),
    path('today/', todays_orders, name='todays-orders'),
    path('next-order-number/', next_order_number, name='next-order-number'),
    path('options/', order_options, name='order-options'),
    path('delivery-locations/', DeliveryLocationListAPIView.as_view(), name='delivery-locations'),
    path('status-history/', OrderStatusHistoryAPIView.as_view(), name='order-status-history'),
    path('stats/', order_stats, name='order-stats'),
    path('stats/quick/', quick_stats, name='quick-stats'),
    path('<str:order_number>/', OrderRetrieveUpdateDestroyAPIView.as_view(), name='order-detail'),
    path('<str:order_number>/status/', OrderStatusUpdateAPIView.as_view(), name='order-status-update'),
]

