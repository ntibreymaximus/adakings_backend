from django.urls import path
from .views import ComprehensiveStatsAPIView

app_name = 'stats'

urlpatterns = [
    path('dashboard/', ComprehensiveStatsAPIView.as_view(), name='dashboard-stats'),
]
