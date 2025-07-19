from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, Avg, Min, Case, When, Value, IntegerField
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from datetime import timedelta, datetime
from decimal import Decimal
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
import logging

from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment, PaymentTransaction
from apps.menu.models import MenuItem
from apps.audit.models import AuditLog
from apps.deliveries.models import DeliveryRider, OrderAssignment
from apps.users.models import CustomUser

logger = logging.getLogger(__name__)


class ComprehensiveStatsAPIView(APIView):
    """API view for comprehensive dashboard statistics"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Dashboard Statistics",
        description="Returns comprehensive dashboard statistics including orders, revenue, customers, and more.",
        parameters=[
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Start date for filtering (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='End date for filtering (YYYY-MM-DD)',
                required=False
            ),
        ],
        responses={
            200: inline_serializer(
                name='DashboardStatsResponse',
                fields={
                    'totalOrders': serializers.IntegerField(),
                    'pendingOrders': serializers.IntegerField(),
                    'completedOrders': serializers.IntegerField(),
                    'cancelledOrders': serializers.IntegerField(),
                    'totalRevenue': serializers.DecimalField(max_digits=10, decimal_places=2),
                    'todayRevenue': serializers.DecimalField(max_digits=10, decimal_places=2),
                    'monthlyRevenue': serializers.DecimalField(max_digits=10, decimal_places=2),
                    'totalCustomers': serializers.IntegerField(),
                    'newCustomers': serializers.IntegerField(),
                    'topProducts': serializers.ListField(
                        child=serializers.DictField()
                    ),
                    'recentOrders': serializers.ListField(
                        child=serializers.DictField()
                    ),
                    'monthlyData': serializers.ListField(
                        child=serializers.DictField()
                    ),
                    'ordersByStatus': serializers.DictField(),
                    'paymentMethods': serializers.DictField(),
                    'hourlyOrders': serializers.ListField(
                        child=serializers.DictField()
                    ),
                    'deliveryStats': serializers.DictField(),
                }
            )
        },
        tags=['Statistics']
    )
    def get(self, request):
        # Get date parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Parse dates or use defaults
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                start_date = timezone.now().date() - timedelta(days=30)
        else:
            start_date = timezone.now().date() - timedelta(days=30)
            
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()
        else:
            end_date = timezone.now().date()
        
        # Convert to datetime with timezone
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        # Get current time and date ranges
        now = timezone.now()
        today = now.date()
        month_start = today.replace(day=1)
        
        # Base queryset for date range
        orders_in_range = Order.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        )
        
        # Order statistics
        total_orders = orders_in_range.count()
        pending_orders = orders_in_range.filter(status='Pending').count()
        # Count Accepted, Ready, and Out for Delivery as processing
        processing_orders = orders_in_range.filter(
            status__in=['Accepted', 'Ready', 'Out for Delivery']
        ).count()
        # Fulfilled is the same as Completed in the database
        fulfilled_orders = orders_in_range.filter(status='Fulfilled').count()
        cancelled_orders = orders_in_range.filter(status='Cancelled').count()
        
        # Revenue statistics
        total_revenue = orders_in_range.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0.00')
        
        today_revenue = Order.objects.filter(
            created_at__date=today
        ).aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0.00')
        
        monthly_revenue = Order.objects.filter(
            created_at__date__gte=month_start
        ).aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0.00')
        
        # Customer statistics
        # Count unique customers by phone number
        total_customers = Order.objects.filter(
            customer_phone__isnull=False
        ).values('customer_phone').distinct().count()
        
        # New customers (first order in date range)
        new_customers = orders_in_range.filter(
            customer_phone__isnull=False
        ).values('customer_phone').annotate(
            first_order=Min('created_at')
        ).filter(
            first_order__gte=start_datetime
        ).count()
        
        # Top products
        top_products_data = OrderItem.objects.filter(
            order__in=orders_in_range
        ).values(
            'menu_item__name'
        ).annotate(
            quantity=Sum('quantity'),
            revenue=Sum('subtotal')
        ).order_by('-revenue')[:10]
        
        top_products = [
            {
                'name': item['menu_item__name'] or 'Unknown Item',
                'quantity': item['quantity'],
                'revenue': float(item['revenue'] or 0)
            }
            for item in top_products_data
        ]
        
        # Recent orders
        recent_orders_qs = Order.objects.select_related(
            'delivery_location'
        ).order_by('-created_at')[:10]
        
        recent_orders = [
            {
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_phone or 'Guest',
                'total': float(order.total_price),
                'status': order.status,
                'created_at': order.created_at.isoformat()
            }
            for order in recent_orders_qs
        ]
        
        # Monthly revenue data (for charts)
        monthly_data = Order.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('total_price'),
            orders=Count('id')
        ).order_by('month')
        
        monthly_chart_data = [
            {
                'month': item['month'].strftime('%B %Y'),
                'revenue': float(item['revenue'] or 0),
                'orders': item['orders']
            }
            for item in monthly_data
        ]
        
        # Orders by status
        orders_by_status = orders_in_range.values('status').annotate(
            count=Count('id')
        )
        
        status_dict = {item['status']: item['count'] for item in orders_by_status}
        
        # Payment methods statistics
        payment_methods_data = Payment.objects.filter(
            order__in=orders_in_range,
            status='success'
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        payment_methods = {
            item['payment_method']: {
                'count': item['count'],
                'total': float(item['total'] or 0)
            }
            for item in payment_methods_data
        }
        
        # Hourly orders (for today)
        hourly_orders_data = Order.objects.filter(
            created_at__date=today
        ).annotate(
            hour=TruncHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        # Fill in missing hours with 0
        hourly_dict = {item['hour'].hour: item['count'] for item in hourly_orders_data}
        hourly_orders = [
            {
                'hour': hour,
                'count': hourly_dict.get(hour, 0)
            }
            for hour in range(24)
        ]
        
        # Delivery statistics
        active_riders = DeliveryRider.objects.filter(status='active').count()
        available_riders = DeliveryRider.objects.filter(
            status='active',
            is_available=True
        ).count()
        
        deliveries_today = OrderAssignment.objects.filter(
            order__created_at__date=today
        ).count()
        
        pending_deliveries = OrderAssignment.objects.filter(
            status__in=['assigned', 'accepted', 'picked_up', 'in_transit']
        ).count()
        
        delivery_stats = {
            'activeRiders': active_riders,
            'availableRiders': available_riders,
            'deliveriesToday': deliveries_today,
            'pendingDeliveries': pending_deliveries
        }
        
        # Compile all statistics
        stats = {
            'totalOrders': total_orders,
            'pendingOrders': pending_orders,
            'processingOrders': processing_orders,
            'fulfilledOrders': fulfilled_orders,
            'cancelledOrders': cancelled_orders,
            # Keep completedOrders for backward compatibility
            'completedOrders': fulfilled_orders,
            'totalRevenue': float(total_revenue),
            'todayRevenue': float(today_revenue),
            'monthlyRevenue': float(monthly_revenue),
            'totalCustomers': total_customers,
            'newCustomers': new_customers,
            'topProducts': top_products,
            'recentOrders': recent_orders,
            'monthlyData': monthly_chart_data,
            'ordersByStatus': status_dict,
            'paymentMethods': payment_methods,
            'hourlyOrders': hourly_orders,
            'deliveryStats': delivery_stats,
        }
        
        return Response(stats)
