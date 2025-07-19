from django.urls import path
from .views import ComprehensiveStatsAPIView, MenuItemsServedAPIView

app_name = 'stats'

urlpatterns = [
    path('dashboard/', ComprehensiveStatsAPIView.as_view(), name='dashboard-stats'),
    path('menu-items-served/', MenuItemsServedAPIView.as_view(), name='menu-items-served'),
]
