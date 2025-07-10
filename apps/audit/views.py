from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from rest_framework import generics, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.users.permissions import IsAdminOrSuperuser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.pagination import PageNumberPagination

from .models import AuditLog, UserActivitySummary
from .serializers import AuditLogSerializer, UserActivitySummarySerializer


class AuditLogPagination(PageNumberPagination):
    """Custom pagination for audit logs"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


@extend_schema(
    tags=['Audit']
)
class AuditLogListAPIView(generics.ListAPIView):
    """
    List all audit logs with filtering and search capabilities.
    Only accessible by admin and superuser roles.
    """
    serializer_class = AuditLogSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrSuperuser]
    pagination_class = AuditLogPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['object_repr', 'user__username', 'user__email', 'ip_address']
    ordering_fields = ['timestamp', 'action', 'user__username']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user', 'content_type')
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            try:
                queryset = queryset.filter(user_id=int(user_id))
            except (ValueError, TypeError):
                pass
        
        # Filter by app/model
        app_label = self.request.query_params.get('app')
        if app_label:
            queryset = queryset.filter(app_label=app_label)
        
        model_name = self.request.query_params.get('model')
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=end)
            except ValueError:
                pass
        
        # Filter by days back (convenience filter)
        days_back = self.request.query_params.get('days')
        if days_back:
            try:
                days = int(days_back)
                cutoff = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(timestamp__gte=cutoff)
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    @extend_schema(
        summary="List Audit Logs",
        description="Retrieve a paginated list of audit logs with filtering options.",
        parameters=[
            OpenApiParameter('action', OpenApiTypes.STR, description='Filter by action type'),
            OpenApiParameter('user', OpenApiTypes.INT, description='Filter by user ID'),
            OpenApiParameter('app', OpenApiTypes.STR, description='Filter by app label'),
            OpenApiParameter('model', OpenApiTypes.STR, description='Filter by model name'),
            OpenApiParameter('start_date', OpenApiTypes.DATETIME, description='Filter logs after this date'),
            OpenApiParameter('end_date', OpenApiTypes.DATETIME, description='Filter logs before this date'),
            OpenApiParameter('days', OpenApiTypes.INT, description='Filter logs from last X days'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Search in object representation, username, email, or IP'),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema(
    tags=['Audit']
)
class AuditLogDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve a specific audit log entry.
    Only accessible by admin and superuser roles.
    """
    queryset = AuditLog.objects.select_related('user', 'content_type')
    serializer_class = AuditLogSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrSuperuser]
    
    @extend_schema(
        summary="Retrieve Audit Log",
        description="Retrieve detailed information about a specific audit log entry."
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema(
    tags=['Audit'],
    summary="Get Audit Dashboard Stats",
    description="Get audit log statistics for dashboard display."
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrSuperuser])
def audit_dashboard_stats(request):
    """Get audit statistics for dashboard"""
    
    # Get date ranges
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Basic stats
    total_logs = AuditLog.objects.count()
    today_logs = AuditLog.objects.filter(timestamp__date=today).count()
    week_logs = AuditLog.objects.filter(timestamp__gte=week_ago).count()
    month_logs = AuditLog.objects.filter(timestamp__gte=month_ago).count()
    
    # Action breakdown (last 30 days)
    action_stats = AuditLog.objects.filter(
        timestamp__gte=month_ago
    ).values('action').annotate(
        count=Count('action')
    ).order_by('-count')
    
    # Top users by activity (last 7 days)
    user_stats = AuditLog.objects.filter(
        timestamp__gte=week_ago,
        user__isnull=False
    ).values(
        'user__username', 'user__first_name', 'user__last_name'
    ).annotate(
        count=Count('user')
    ).order_by('-count')[:10]
    
    # Model activity breakdown (last 30 days)
    model_stats = AuditLog.objects.filter(
        timestamp__gte=month_ago
    ).values('app_label', 'model_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Recent critical actions
    critical_actions = AuditLog.objects.filter(
        action__in=['delete', 'payment', 'refund'],
        timestamp__gte=week_ago
    ).select_related('user')[:20]
    
    return Response({
        'summary': {
            'total_logs': total_logs,
            'today_logs': today_logs,
            'week_logs': week_logs,
            'month_logs': month_logs,
        },
        'action_breakdown': [
            {
                'action': item['action'],
                'action_display': dict(AuditLog.ACTION_CHOICES).get(item['action'], item['action']),
                'count': item['count']
            }
            for item in action_stats
        ],
        'top_users': [
            {
                'username': item['user__username'],
                'name': f"{item['user__first_name']} {item['user__last_name']}".strip() or item['user__username'],
                'action_count': item['count']
            }
            for item in user_stats
        ],
        'model_activity': [
            {
                'app': item['app_label'],
                'model': item['model_name'],
                'display_name': f"{item['app_label'].title()} {item['model_name'].title()}",
                'count': item['count']
            }
            for item in model_stats
        ],
        'recent_critical': AuditLogSerializer(critical_actions, many=True).data
    })


@extend_schema(
    tags=['Audit'],
    summary="Get User Activity",
    description="Get activity logs for a specific user."
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrSuperuser])
def user_activity(request, user_id):
    """Get activity logs for a specific user"""
    
    days = request.GET.get('days', 30)
    try:
        days = int(days)
    except (ValueError, TypeError):
        days = 30
    
    cutoff = timezone.now() - timedelta(days=days)
    
    # Get user's audit logs
    logs = AuditLog.objects.filter(
        user_id=user_id,
        timestamp__gte=cutoff
    ).select_related('content_type').order_by('-timestamp')
    
    # Get activity summary
    summary = logs.values('action').annotate(
        count=Count('action')
    ).order_by('-count')
    
    return Response({
        'user_id': user_id,
        'period_days': days,
        'total_actions': logs.count(),
        'summary': [
            {
                'action': item['action'],
                'action_display': dict(AuditLog.ACTION_CHOICES).get(item['action'], item['action']),
                'count': item['count']
            }
            for item in summary
        ],
        'recent_logs': AuditLogSerializer(logs[:50], many=True).data
    })


@extend_schema(
    tags=['Audit'],
    summary="Get Order Activity Summary",
    description="Get simplified activity summary for a specific order - first and latest log only."
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_activity_summary(request, order_id):
    """Get simplified activity summary for a specific order"""
    from apps.orders.models import Order
    from django.contrib.contenttypes.models import ContentType
    
    try:
        # Try to get order by ID first, then by order_number
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            order = Order.objects.get(order_number=order_id)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get the content type for Order model
    order_content_type = ContentType.objects.get_for_model(Order)
    
    # Get order-related logs
    order_logs = AuditLog.objects.filter(
        content_type=order_content_type,
        object_id=order.id
    ).select_related('user').order_by('timestamp')
    
    # Get payment-related logs for this order
    payment_logs = AuditLog.objects.filter(
        app_label='payments',
        changes__order_id=order.id
    ).select_related('user').order_by('timestamp')
    
    # Combine logs
    all_logs = list(order_logs) + list(payment_logs)
    all_logs.sort(key=lambda x: x.timestamp)
    
    # Prepare response
    result = {
        'order_id': order.id,
        'order_number': order.order_number,
        'first_log': None,
        'latest_log': None,
        'total_activities': len(all_logs)
    }
    
    if all_logs:
        # First log (creation)
        first_log = all_logs[0]
        result['first_log'] = {
            'action': first_log.get_action_display(),
            'user_name': first_log.user.get_full_name() or first_log.user.username if first_log.user else 'System',
            'username': first_log.user.username if first_log.user else 'system',
            'timestamp': first_log.timestamp,
            'time_ago': get_time_ago(first_log.timestamp)
        }
        
        # Latest log (most recent activity)
        if len(all_logs) > 1:
            latest_log = all_logs[-1]
            result['latest_log'] = {
                'action': latest_log.get_action_display(),
                'user_name': latest_log.user.get_full_name() or latest_log.user.username if latest_log.user else 'System',
                'username': latest_log.user.username if latest_log.user else 'system',
                'timestamp': latest_log.timestamp,
                'time_ago': get_time_ago(latest_log.timestamp)
            }
        else:
            # If only one log, it's both first and latest
            result['latest_log'] = result['first_log']
    
    return Response(result)


def get_time_ago(timestamp):
    """Helper function to get human-readable time"""
    from django.utils.timesince import timesince
    from django.utils import timezone
    
    now = timezone.now()
    time_diff = now - timestamp
    
    if time_diff.total_seconds() < 30:
        return "Just now"
    
    return timesince(timestamp, now) + " ago"


@extend_schema(
    tags=['Audit']
)
class UserActivitySummaryListAPIView(generics.ListAPIView):
    """
    List user activity summaries.
    Only accessible by admin and superuser roles.
    """
    serializer_class = UserActivitySummarySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrSuperuser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date', 'total_actions', 'user__username']
    ordering = ['-date', 'user__username']
    
    def get_queryset(self):
        queryset = UserActivitySummary.objects.select_related('user')
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            try:
                queryset = queryset.filter(user_id=int(user_id))
            except (ValueError, TypeError):
                pass
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end)
            except ValueError:
                pass
        
        return queryset
    
    @extend_schema(
        summary="List User Activity Summaries",
        description="Retrieve user activity summaries with optional filtering.",
        parameters=[
            OpenApiParameter('user', OpenApiTypes.INT, description='Filter by user ID'),
            OpenApiParameter('start_date', OpenApiTypes.DATE, description='Filter summaries after this date (YYYY-MM-DD)'),
            OpenApiParameter('end_date', OpenApiTypes.DATE, description='Filter summaries before this date (YYYY-MM-DD)'),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
