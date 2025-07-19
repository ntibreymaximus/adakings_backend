from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, Avg, Min, Case, When, Value, IntegerField, CharField
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
        
        # Customer statistics (apply date filter)
        # Count unique customers by phone number in the date range
        total_customers = orders_in_range.filter(
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
        
        # Recent orders (apply date filter)
        recent_orders_qs = orders_in_range.select_related(
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
            status='completed'
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Initialize all payment methods with zero values
        from apps.payments.models import Payment as PaymentModel
        payment_methods = {}
        for method_code, method_name in PaymentModel.PAYMENT_METHOD_CHOICES:
            payment_methods[method_code] = {
                'count': 0,
                'total': 0.0
            }
        
        # Update with actual data
        for item in payment_methods_data:
            payment_methods[item['payment_method']] = {
                'count': item['count'],
                'total': float(item['total'] or 0)
            }
        
        # Refund statistics - include both actual pending refunds AND overpayments due
        # Actual pending refund records
        pending_refund_records = Payment.objects.filter(
            order__in=orders_in_range,
            payment_type='refund',
            status__in=['pending', 'processing']
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Overpayments that need refunds (calculate refund_amount for all orders)
        total_pending_refunds = Decimal('0.00')
        pending_refund_count = pending_refund_records['count'] or 0
        
        # Add refunds due from overpayments
        for order in orders_in_range:
            try:
                refund_due = order.refund_amount()
                if refund_due > Decimal('0.00'):
                    total_pending_refunds += refund_due
                    # Only count as pending if there's no existing refund record
                    has_pending_refund = Payment.objects.filter(
                        order=order,
                        payment_type='refund',
                        status__in=['pending', 'processing']
                    ).exists()
                    if not has_pending_refund:
                        pending_refund_count += 1
            except Exception as e:
                logger.error(f"Error calculating refund for order {order.order_number}: {e}")
                continue
        
        # Add any existing pending refund amounts
        total_pending_refunds += Decimal(str(pending_refund_records['total'] or 0))
        
        completed_refunds_data = Payment.objects.filter(
            order__in=orders_in_range,
            payment_type='refund',
            status='completed'
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Add refund data to payment methods
        payment_methods['PENDING_REFUNDS'] = {
            'count': pending_refund_count,
            'total': float(total_pending_refunds)
        }
        
        payment_methods['COMPLETED_REFUNDS'] = {
            'count': completed_refunds_data['count'] or 0,
            'total': float(completed_refunds_data['total'] or 0)
        }
        
        # Hourly orders (apply date filter - use filtered date range if single day, otherwise today)
        hourly_date = start_date if start_date == end_date else today
        hourly_orders_data = Order.objects.filter(
            created_at__date=hourly_date
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
        
        # Pending deliveries (assigned, accepted, picked_up, in_transit)
        pending_deliveries = OrderAssignment.objects.filter(
            status__in=['assigned', 'accepted', 'picked_up', 'in_transit'],
            order__created_at__gte=start_datetime,
            order__created_at__lte=end_datetime
        ).count()
        
        # Completed deliveries (delivered status)
        completed_deliveries = OrderAssignment.objects.filter(
            status='delivered',
            order__created_at__gte=start_datetime,
            order__created_at__lte=end_datetime
        ).count()
        
        # Completed pickups (orders with Pickup delivery_type that are fulfilled)
        completed_pickups = orders_in_range.filter(
            delivery_type='Pickup',
            status='Fulfilled'
        ).count()
        
        # Top delivery locations (exclude pickup orders and include both regular and custom locations)
        top_delivery_locations_data = orders_in_range.filter(
            delivery_type='Delivery'
        ).exclude(
            delivery_location__isnull=True,
            custom_delivery_location__isnull=True
        ).annotate(
            # Use delivery_location name or custom_delivery_location as the location name
            location_name=Case(
                When(delivery_location__isnull=False, then='delivery_location__name'),
                default='custom_delivery_location',
                output_field=CharField()
            )
        ).values(
            'location_name'
        ).annotate(
            count=Count('id'),
            total_revenue=Sum('total_price')
        ).order_by('-count')[:5]
        
        top_delivery_locations = [
            {
                'location': item['location_name'],
                'orders': item['count'],
                'revenue': float(item['total_revenue'] or 0)
            }
            for item in top_delivery_locations_data
            if item['location_name']
        ]
        
        delivery_stats = {
            'activeRiders': active_riders,
            'availableRiders': available_riders,
            'pendingDeliveries': pending_deliveries,
            'completedDeliveries': completed_deliveries,
            'completedPickups': completed_pickups,
            'topDeliveryLocations': top_delivery_locations
        }
        
        # Calculate percentage changes for period comparison
        # Get comparison period (same duration before the current period)
        period_duration = (end_date - start_date).days + 1  # +1 to include both start and end dates
        comparison_end = start_date - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_duration - 1)
        
        comparison_start_datetime = timezone.make_aware(datetime.combine(comparison_start, datetime.min.time()))
        comparison_end_datetime = timezone.make_aware(datetime.combine(comparison_end, datetime.max.time()))
        
        # Previous period orders and revenue
        previous_orders = Order.objects.filter(
            created_at__gte=comparison_start_datetime,
            created_at__lte=comparison_end_datetime
        ).count()
        
        previous_revenue = Order.objects.filter(
            created_at__gte=comparison_start_datetime,
            created_at__lte=comparison_end_datetime
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        
        # Calculate percentage changes
        def calculate_percentage_change(current, previous):
            if not previous or previous == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - previous) / previous) * 100, 1)
        
        orders_percentage_change = calculate_percentage_change(total_orders, previous_orders)
        revenue_percentage_change = calculate_percentage_change(float(total_revenue), float(previous_revenue))
        
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
            # Percentage changes
            'ordersPercentageChange': orders_percentage_change,
            'revenuePercentageChange': revenue_percentage_change,
        }
        
        return Response(stats)


class MenuItemsServedAPIView(APIView):
    """API view for menu items served statistics"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Menu Items Served Statistics",
        description="Returns statistics about menu items served for a specific date.",
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Date for filtering (YYYY-MM-DD). Defaults to today.',
                required=False
            ),
        ],
        responses={
            200: inline_serializer(
                name='MenuItemsServedResponse',
                fields={
                    'totalItemsServed': serializers.IntegerField(),
                    'uniqueItemsServed': serializers.IntegerField(),
                    'topItems': serializers.ListField(
                        child=serializers.DictField()
                    ),
                }
            )
        },
        tags=['Statistics']
    )
    def get(self, request):
        # Get date parameter
        date_str = request.GET.get('date')
        
        # Parse date or use today
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = timezone.now().date()
        else:
            target_date = timezone.now().date()
        
        # Convert to datetime with timezone
        start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))
        
        # Get all regular menu items (not extras)
        all_menu_items = MenuItem.objects.filter(is_extra=False)
        
        # Initialize all menu items with 0 count
        items_count = {item.name: 0 for item in all_menu_items}
        
        # Get orders for the specific date
        orders = Order.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        )
        
        total_items_served = 0
        
        # Calculate menu items statistics from orders
        for order in orders:
            order_items = OrderItem.objects.filter(order=order)
            for item in order_items:
                item_name = item.menu_item.name if item.menu_item else 'Unknown Item'
                quantity = item.quantity or 0
                
                # Only count if the item exists in our menu
                if item_name in items_count:
                    items_count[item_name] += quantity
                    total_items_served += quantity
        
        # Get all items sorted by count (descending), including items with 0 count
        top_items = sorted(
            [{'name': name, 'count': count} for name, count in items_count.items()],
            key=lambda x: x['count'],
            reverse=True
        )
        
        stats = {
            'totalItemsServed': total_items_served,
            'uniqueItemsServed': len(all_menu_items),  # Total number of menu items
            'topItems': top_items
        }
        
        return Response(stats)
