from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeliveryRiderViewSet, OrderAssignmentViewSet, 
    AssignRiderToOrderView, PublicDeliveryTrackingView,
    DeliveryLocationViewSet
)

router = DefaultRouter()
router.register(r'riders', DeliveryRiderViewSet, basename='delivery-riders')
router.register(r'assignments', OrderAssignmentViewSet, basename='order-assignments')
router.register(r'locations', DeliveryLocationViewSet, basename='delivery-locations')

urlpatterns = [
    path('', include(router.urls)),
    path('orders/<str:order_id>/assign-rider/', 
         AssignRiderToOrderView.as_view({'post': 'create'}), 
         name='assign-rider-to-order'),
    path('track/<str:order_number>/', 
         PublicDeliveryTrackingView.as_view({'get': 'retrieve'}), 
         name='public-delivery-tracking'),
]
