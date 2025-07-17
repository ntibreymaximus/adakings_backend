from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import generics, status, filters, serializers
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer
from apps.users.permissions import IsAdminOrFrontdesk, IsAdminOrFrontdeskNoDelete
from .models import Order, OrderItem
from apps.deliveries.models import DeliveryLocation
from .serializers import OrderSerializer, OrderStatusUpdateSerializer, DeliveryLocationSerializer
from .serializers_bolt_wix import BoltOrderSerializer
from apps.audit.utils import log_create, log_update, log_delete, log_status_change, get_model_changes, get_data_changes
from decimal import Decimal


class OrderListPagination(PageNumberPagination):
    """
    Optimized pagination for fast loading.
    """
    page_size = 100  # Default page size for fast loading
    page_size_query_param = 'page_size'
    max_page_size = 500  # Reduced for better performance


@extend_schema(
    summary="Get Next Order Number",
    description="Returns the next available order number in the sequence (e.g., ADA-0001).",
    responses={200: inline_serializer(
        name='NextOrderNumber',
        fields={
            'next_order_number': serializers.CharField(),
        }
    )},
    tags=['Orders']
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def next_order_number(request):
    """Get the next available order number for preview purposes"""
    from django.utils import timezone
    
    # Get current date in DDMMYY format
    date_part = timezone.now().strftime("%d%m%y")
    
    # Get all orders with the same date part
    existing_orders = Order.objects.filter(
        order_number__startswith=date_part
    ).order_by('-order_number')
    
    # Extract all existing sequence numbers for today
    existing_numbers = set()
    for order in existing_orders:
        try:
            seq_num = int(order.order_number.split('-')[1])
            existing_numbers.add(seq_num)
        except (IndexError, ValueError):
            continue
    
    # Find the next available sequence number
    seq_number = 1
    while seq_number in existing_numbers:
        seq_number += 1
    
    # Return the next available order number
    return Response({'next_order_number': f'{date_part}-{seq_number:03d}'})

@extend_schema(
    summary="Get Today's Orders",
    description="Returns all orders for today. Optimized for instant loading.",
    responses={200: OrderSerializer(many=True)},
    tags=['Orders']
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def todays_orders(request):
    """Fast endpoint for today's orders only"""
    from django.utils import timezone
    from .serializers import OrderSerializer
    
    today = timezone.now().date()
    
    # Get today's orders with optimized query
    orders = Order.objects.filter(
        created_at__date=today
    ).select_related(
        'delivery_location'
    ).prefetch_related(
        'items__menu_item',
        'payments'
    ).order_by('-created_at')
    
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@extend_schema( # Moved from get_queryset to class level
    summary="List and Create Orders",
    description="Allows admin users to list all orders or create new ones. Supports filtering by date and search term. Note: Customer name and phone are required for delivery orders but optional for pickup orders.",
    parameters=[
        OpenApiParameter(
            name='date',
            description='Filter by date (YYYY-MM-DD)',
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name='search',
            description='Search in customer name, phone, order number, or location',
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name='ordering',
            description='Order by fields (e.g., created_at, total_price, status)',
            required=False,
            type=OpenApiTypes.STR
        ),
    ],
    tags=['Orders']
)
class OrderListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Remove pagination to show all orders
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_phone', 'order_number', 'delivery_location__name']
    ordering_fields = ['created_at', 'total_price', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use appropriate serializer based on order type"""
        if self.request.method == 'POST':
            # Check if this is a Bolt/Wix order based on delivery_location
            delivery_location = self.request.data.get('delivery_location')
            
            # Try to get the DeliveryLocation object if ID is provided
            if delivery_location:
                try:
                    if isinstance(delivery_location, int) or (isinstance(delivery_location, str) and delivery_location.isdigit()):
                        # It's an ID, fetch the location
                        location = DeliveryLocation.objects.get(id=int(delivery_location))
                        if location.name == "Bolt Delivery":
                            return BoltOrderSerializer
                    elif isinstance(delivery_location, str):
                        # It's a name, check directly
                        if delivery_location == "Bolt Delivery":
                            return BoltOrderSerializer
                except DeliveryLocation.DoesNotExist:
                    pass
        
        return self.serializer_class
    
    def perform_create(self, serializer):
        """Log order creation"""
        order = serializer.save()
        
        # Log the order creation
        log_create(
            user=self.request.user,
            obj=order,
            request=self.request,
            extra_data={
                'description': f"Created order {order.order_number} for {order.customer_phone or 'Walk-in'}",
                'order_type': order.delivery_type,
                'total_amount': str(order.total_price),
                'items_count': order.items.count()
            }
        )
    
    # @extend_schema decorator was here, moved to class level
    def get_queryset(self):
        # Optimize queryset with select_related and prefetch_related for instant loading
        queryset = Order.objects.select_related(
            'delivery_location'
        ).prefetch_related(
            'items__menu_item',
            'payments'
        )

        # Date filtering
        date_filter = self.request.query_params.get('date')
        if date_filter:
            try:
                target_date = timezone.datetime.strptime(date_filter, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date=target_date)
            except ValueError:
                pass  # Invalid date format, ignore filter

        return queryset

@extend_schema(
    summary="Manage Individual Orders", # Added summary
    description="Allows admin users to retrieve, update, or delete a specific order by its order number.", # Added description
    tags=['Orders']
)
class OrderRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.select_related(
        'delivery_location'
    ).prefetch_related(
        'items__menu_item',
        'payments'
    )
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrFrontdeskNoDelete]  # Admin can do everything, frontdesk can view/update but not delete
    lookup_field = 'order_number'
    lookup_url_kwarg = 'order_number'

    @extend_schema(
        summary="Retrieve an Order", # Changed from generic "Retrieve, Update, or Delete..."
        description="Retrieves the details of a specific order by its order number.", # Made description more specific to GET
        tags=['Orders']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update an Order",
        description="Updates an existing order with new information. Can modify order details and items.",
        tags=['Orders']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        """Log order updates"""
        # Get the original data
        order = self.get_object()
        original_data = OrderSerializer(order).data
        
        # Save the updated order
        updated_order = serializer.save()
        
        # Get changes
        updated_data = OrderSerializer(updated_order).data
        changes = get_data_changes(original_data, updated_data)
        
        # Extract old and new values from changes
        old_values = {field: change['old'] for field, change in changes.items()}
        new_values = {field: change['new'] for field, change in changes.items()}
        
        # Log the update
        log_update(
            user=self.request.user,
            obj=updated_order,
            old_values=old_values,
            new_values=new_values,
            request=self.request
        )

    @extend_schema(
        summary="Partially Update an Order",
        description="Partially updates an existing order. Only provided fields will be modified.",
        tags=['Orders']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete an Order",
        description="Deletes an existing order. This action cannot be undone.",
        tags=['Orders']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def perform_destroy(self, instance):
        """Log order deletion"""
        # Capture order details before deletion
        order_details = {
            'description': f"Deleted order {instance.order_number}",
            'order_number': instance.order_number,
            'customer_phone': instance.customer_phone,
            'total_price': str(instance.total_price),
            'status': instance.status,
            'payment_status': instance.get_payment_status()
        }
        
        # Log the deletion
        log_delete(
            user=self.request.user,
            obj=instance,
            request=self.request,
            extra_data=order_details
        )
        
        # Perform the actual deletion
        super().perform_destroy(instance)

@extend_schema(
    summary="Manage Order Status", # Added summary
    description="Allows authorized staff (admin or frontdesk) to update the status of a specific order.", # Added description
    tags=['Orders']
)
class OrderStatusUpdateAPIView(generics.UpdateAPIView):
    queryset = Order.objects.select_related('delivery_location')
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsAdminOrFrontdesk]  # Admin and frontdesk staff can update order status
    lookup_field = 'order_number'
    lookup_url_kwarg = 'order_number'

    @extend_schema(
        summary="Update Order Status",
        description="Updates the status of an existing order. Admin or frontdesk staff can perform this action.",
        tags=['Orders']
    )
    def update(self, request, *args, **kwargs):
        # Permission is now handled by IsAdminOrFrontdesk class
        return super().update(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        """Log order status changes"""
        # Get the original status
        order = self.get_object()
        old_status = order.status
        
        # Save the updated order
        updated_order = serializer.save()
        new_status = updated_order.status
        
        # Log the status change
        log_status_change(
            user=self.request.user,
            obj=updated_order,
            old_status=old_status,
            new_status=new_status,
            request=self.request,
            extra_data={
                'description': f"Changed order {updated_order.order_number} status from {old_status} to {new_status}",
                'order_type': updated_order.delivery_type,
                'total_amount': str(updated_order.total_price)
            }
        )

    def patch(self, request, *args, **kwargs):
        # Redirect PATCH to PUT since we're only updating status
        return self.update(request, *args, **kwargs)


@extend_schema(
    summary="List Active Delivery Locations",
    description="Returns a list of all active delivery locations with their fees.",
    tags=['Orders']
)
class DeliveryLocationListAPIView(generics.ListAPIView):
    serializer_class = DeliveryLocationSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access for frontend
    
    def get_queryset(self):
        # Ensure delivery locations are loaded and up-to-date
        from apps.deliveries.utils import ensure_delivery_locations_loaded
        ensure_delivery_locations_loaded()
        
        # Only return active delivery locations
        return DeliveryLocation.objects.filter(is_active=True).order_by('name')


@extend_schema(
    summary="Order Status History",
    description="Returns a simplified status history for orders. Since the system doesn't track detailed status changes, this provides order creation and last update timestamps.",
    parameters=[
        OpenApiParameter(
            name='order_number',
            description='Filter by specific order number',
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name='days',
            description='Number of days to look back (default: 7)',
            required=False,
            type=OpenApiTypes.INT
        ),
    ],
    tags=['Orders']
)
class OrderStatusHistoryAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer  # Add serializer class
    permission_classes = [IsAdminOrFrontdesk]
    authentication_classes = [JWTAuthentication]
    
    def get_queryset(self):
        queryset = Order.objects.select_related('delivery_location').order_by('-updated_at')
        
        # Filter by order number if provided
        order_number = self.request.query_params.get('order_number')
        if order_number:
            queryset = queryset.filter(order_number__icontains=order_number)
        
        # Filter by days if provided (default to 7 days)
        days = self.request.query_params.get('days', '7')
        try:
            days_int = int(days)
            cutoff_date = timezone.now() - timezone.timedelta(days=days_int)
            queryset = queryset.filter(updated_at__gte=cutoff_date)
        except ValueError:
            pass  # Invalid days parameter, ignore filter
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        status_history = []
        for order in queryset:
            # Create status history entry
            history_entry = {
                'order_number': order.order_number,
                'customer_phone': order.customer_phone,
                'current_status': order.status,
                'delivery_type': order.delivery_type,
                'delivery_location': order.get_effective_delivery_location_name(),
                'total_price': float(order.total_price),
                'payment_status': order.get_payment_status(),
                'amount_paid': float(order.amount_paid()),
                'balance_due': float(order.balance_due()),
                'created_at': order.created_at.isoformat(),
                'last_updated': order.updated_at.isoformat(),
                'time_ago': order.time_ago(),
                'status_changes': [
                    {
                        'status': 'Created',
                        'timestamp': order.created_at.isoformat(),
                        'is_current': False
                    },
                    {
                        'status': order.status,
                        'timestamp': order.updated_at.isoformat(),
                        'is_current': True
                    }
                ]
            }
            status_history.append(history_entry)
        
        return Response({
            'count': len(status_history),
            'results': status_history
        })


@extend_schema(
    summary="Get Order Options",
    description="Returns available options for orders including status choices, delivery types, and other field options.",
    responses={200: inline_serializer(
        name='OrderOptions',
        fields={
            'status_choices': serializers.ListField(
                child=inline_serializer(
                    name='StatusChoice',
                    fields={
                        'value': serializers.CharField(),
                        'display': serializers.CharField(),
                    }
                )
            ),
            'delivery_type_choices': serializers.ListField(
                child=inline_serializer(
                    name='DeliveryTypeChoice',
                    fields={
                        'value': serializers.CharField(),
                        'display': serializers.CharField(),
                    }
                )
            ),
        }
    )},
    tags=['Orders']
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unauthenticated access for frontend
def order_options(request):
    """Get available options for order fields"""
    # Get status choices from the Order model
    status_choices = [
        {'value': value, 'display': display} 
        for value, display in Order.STATUS_CHOICES
    ]
    
    # Get delivery type choices
    delivery_type_choices = [
        {'value': value, 'display': display} 
        for value, display in Order.DELIVERY_CHOICES
    ]
    
    return Response({
        'status_choices': status_choices,
        'delivery_type_choices': delivery_type_choices,
    })


@extend_schema(
    summary="Get Order Statistics",
    description="Returns aggregated statistics about orders including refund amounts, payment status, and other metrics.",
    parameters=[
        OpenApiParameter(
            name='date',
            description='Filter by specific date (YYYY-MM-DD)',
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name='days',
            description='Number of days to look back (default: 30)',
            required=False,
            type=OpenApiTypes.INT
        ),
    ],
    responses={200: inline_serializer(
        name='OrderStats',
        fields={
            'total_orders': serializers.IntegerField(),
            'total_revenue': serializers.DecimalField(max_digits=10, decimal_places=2),
            'total_refunds_due': serializers.DecimalField(max_digits=10, decimal_places=2),
            'payment_status_breakdown': serializers.DictField(),
            'status_breakdown': serializers.DictField(),
            'delivery_type_breakdown': serializers.DictField(),
        }
    )},
    tags=['Orders']
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def order_stats(request):
    """Get order statistics including refund amounts"""
    from django.db.models import Count, Sum, Case, When, Value, IntegerField
    from django.utils import timezone
    from datetime import timedelta
    
    # Get query parameters
    date_filter = request.query_params.get('date')
    days_param = request.query_params.get('days', '30')
    
    # Build base queryset
    queryset = Order.objects.select_related('delivery_location').prefetch_related('payments')
    
    # Apply date filtering
    if date_filter:
        try:
            target_date = timezone.datetime.strptime(date_filter, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date=target_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    else:
        # Default to last X days
        try:
            days = int(days_param)
            cutoff_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created_at__gte=cutoff_date)
        except ValueError:
            pass  # Invalid days parameter, ignore filter
    
    # Calculate basic metrics
    total_orders = queryset.count()
    total_revenue = queryset.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
    
    # Calculate total refunds due by iterating through orders (since refund_amount is a method)
    total_refunds_due = Decimal('0.00')
    for order in queryset:
        total_refunds_due += order.refund_amount()
    
    # Payment status breakdown
    payment_status_breakdown = {}
    for order in queryset:
        status = order.get_payment_status()
        payment_status_breakdown[status] = payment_status_breakdown.get(status, 0) + 1
    
    # Order status breakdown
    status_breakdown = dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count'))
    
    # Delivery type breakdown
    delivery_type_breakdown = dict(queryset.values('delivery_type').annotate(count=Count('id')).values_list('delivery_type', 'count'))
    
    return Response({
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_refunds_due': total_refunds_due,
        'payment_status_breakdown': payment_status_breakdown,
        'status_breakdown': status_breakdown,
        'delivery_type_breakdown': delivery_type_breakdown,
        'date_range': {
            'specific_date': date_filter,
            'days_back': days_param if not date_filter else None
        }
    })


@extend_schema(
    summary="Get Quick Statistics",
    description="Returns today's quick statistics including today's orders, today's revenue, pending orders, and monthly revenue.",
    responses={200: inline_serializer(
        name='QuickStats',
        fields={
            'todayOrders': serializers.IntegerField(),
            'todayRevenue': serializers.DecimalField(max_digits=10, decimal_places=2),
            'pendingOrders': serializers.IntegerField(),
            'monthlyRevenue': serializers.DecimalField(max_digits=10, decimal_places=2),
        }
    )},
    tags=['Orders']
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def quick_stats(request):
    """Get today's quick statistics for dashboard"""
    from django.db.models import Sum
    from django.utils import timezone
    from decimal import Decimal
    
    # Get today's date
    today = timezone.now().date()
    
    # Get this month's start date
    month_start = today.replace(day=1)
    
    # Today's orders
    today_orders = Order.objects.filter(created_at__date=today)
    todayOrders = today_orders.count()
    
    # Today's revenue (sum of total_price for today's orders)
    todayRevenue = today_orders.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
    
    # Pending orders (all pending orders, not just today's)
    pendingOrders = Order.objects.filter(status='pending').count()
    
    # Monthly revenue (sum of total_price for this month's orders)
    monthly_orders = Order.objects.filter(created_at__date__gte=month_start)
    monthlyRevenue = monthly_orders.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
    
    return Response({
        'todayOrders': todayOrders,
        'todayRevenue': float(todayRevenue),
        'pendingOrders': pendingOrders,
        'monthlyRevenue': float(monthlyRevenue),
    })
