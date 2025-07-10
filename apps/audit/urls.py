from django.urls import path
from .views import (
    AuditLogListAPIView,
    AuditLogDetailAPIView,
    UserActivitySummaryListAPIView,
    audit_dashboard_stats,
    user_activity,
    order_activity_summary
)

app_name = 'audit_api'

urlpatterns = [
    # Audit log endpoints
    path('logs/', AuditLogListAPIView.as_view(), name='audit-log-list'),
    path('logs/<int:pk>/', AuditLogDetailAPIView.as_view(), name='audit-log-detail'),
    
    # Dashboard and statistics
    path('dashboard/', audit_dashboard_stats, name='audit-dashboard'),
    
    # User activity
    path('users/<int:user_id>/activity/', user_activity, name='user-activity'),
    path('summaries/', UserActivitySummaryListAPIView.as_view(), name='activity-summary-list'),
    
    # Order activity
    path('orders/<str:order_id>/summary/', order_activity_summary, name='order-activity-summary'),
]
