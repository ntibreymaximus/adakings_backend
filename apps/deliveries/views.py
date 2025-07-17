from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from datetime import timedelta

from .models import (
    DeliveryRider, OrderAssignment, DeliveryLocation
)
from .serializers import (
    DeliveryRiderSerializer, DeliveryRiderCreateSerializer,
    OrderAssignmentSerializer, AssignRiderSerializer,
    UpdateAssignmentStatusSerializer, DeliveryLocationSerializer,
    RiderAvailabilitySerializer, DeliveryTrackingSerializer
)
from apps.orders.models import Order
from apps.payments.models import Payment
import logging

logger = logging.getLogger(__name__)


class DeliveryRiderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing delivery riders"""
    queryset = DeliveryRider.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DeliveryRiderCreateSerializer
        return DeliveryRiderSerializer
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get list of available riders"""
        # Use F expressions to compare with max_concurrent_orders field
        from django.db.models import F
        
        riders = self.queryset.filter(
            status='active',
            is_available=True,
            current_orders__lt=F('max_concurrent_orders')  # Dynamic max based on rider settings
        ).order_by('current_orders', '-rating')
        
        serializer = self.get_serializer(riders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_availability(self, request, pk=None):
        """Update rider availability"""
        rider = self.get_object()
        serializer = RiderAvailabilitySerializer(data=request.data)
        
        if serializer.is_valid():
            rider.is_available = serializer.validated_data['is_available']
            if 'status' in serializer.validated_data:
                rider.status = serializer.validated_data['status']
            rider.save()
            return Response(DeliveryRiderSerializer(rider).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def current_assignments(self, request, pk=None):
        """Get current active assignments for a rider"""
        rider = self.get_object()
        assignments = OrderAssignment.objects.filter(
            rider=rider,
            status__in=['assigned', 'accepted', 'picked_up', 'in_transit']
        )
        serializer = OrderAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def earnings(self, request, pk=None):
        """Get rider earnings summary"""
        rider = self.get_object()
        period = request.query_params.get('period', 'week')  # week, month, all
        
        # Calculate date range
        end_date = timezone.now()
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = None
        
        # Get completed assignments
        assignments = OrderAssignment.objects.filter(
            rider=rider,
            status__in=['delivered', 'returned']
        )
        if start_date:
            assignments = assignments.filter(
                delivered_at__gte=start_date
            )
        
        # Calculate summary
        summary = assignments.aggregate(
            total_deliveries=Count('id')
        )
        
        # Add default values for None results
        for key, value in summary.items():
            if value is None:
                summary[key] = 0
        
        summary['period'] = period
        summary['start_date'] = start_date.isoformat() if start_date else None
        summary['end_date'] = end_date.isoformat()
        
        return Response(summary)


class OrderAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order assignments"""
    queryset = OrderAssignment.objects.all()
    serializer_class = OrderAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by rider if provided
        rider_id = self.request.query_params.get('rider_id')
        if rider_id:
            queryset = queryset.filter(rider_id=rider_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(picked_up_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(delivered_at__lte=date_to)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update assignment status"""
        assignment = self.get_object()
        serializer = UpdateAssignmentStatusSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            
            # Validate status transition
            valid_transitions = {
                'assigned': ['accepted', 'cancelled'],
                'accepted': ['picked_up', 'cancelled'],
                'picked_up': ['in_transit', 'cancelled'],
                'in_transit': ['delivered', 'cancelled'],
                'delivered': ['returned'],
                'returned': [],
                'cancelled': []
            }
            
            if new_status not in valid_transitions.get(assignment.status, []):
                return Response(
                    {'error': f'Invalid status transition from {assignment.status} to {new_status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update assignment with transaction
            with transaction.atomic():
                assignment.status = new_status
                
                # Update timestamps and related data
                if new_status == 'accepted':
                    pass  # No timestamp for accepted status
                elif new_status == 'picked_up':
                    assignment.picked_up_at = timezone.now()
                    # Update order status
                    assignment.order.status = 'Out for Delivery'
                    assignment.order.save()
                elif new_status == 'delivered':
                    assignment.delivered_at = timezone.now()
                    # Order status will be updated by signal
                elif new_status == 'returned':
                    # Stats will be updated by signal
                    pass
                elif new_status == 'cancelled':
                    if 'cancellation_reason' in serializer.validated_data:
                        assignment.cancellation_reason = serializer.validated_data['cancellation_reason']
                    # Stats will be updated by signal
                
                # Save notes if provided
                if 'notes' in serializer.validated_data:
                    assignment.delivery_notes = serializer.validated_data['notes']
                
                # Save the assignment - this will trigger the signal
                assignment.save()
            
            return Response(OrderAssignmentSerializer(assignment).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """Get tracking information for an assignment"""
        assignment = self.get_object()
        
        tracking_data = {
            'order_number': assignment.order.order_number,
            'status': assignment.get_status_display(),
            'rider_name': assignment.rider.name if assignment.rider else None,
            'rider_phone': assignment.rider.phone if assignment.rider else None,
            'estimated_time': None,  # TODO: Calculate based on distance and average speed
            'delivery_updates': []
        }
        
        # Add status updates
        updates = []
        if assignment.picked_up_at:
            updates.append({
                'status': 'Order picked up',
                'timestamp': assignment.picked_up_at.isoformat()
            })
        if assignment.delivered_at:
            updates.append({
                'status': 'Delivered to customer',
                'timestamp': assignment.delivered_at.isoformat()
            })
        
        tracking_data['delivery_updates'] = updates
        
        return Response(tracking_data)


class AssignRiderToOrderView(viewsets.ViewSet):
    """ViewSet for assigning riders to orders"""
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, order_id):
        """Assign a rider to an order"""
        logger.info(f"Assign rider request received for order_id: {order_id}")
        logger.info(f"Request data: {request.data}")
        
        # Try to find order by ID first, then by order_number
        try:
            if order_id.isdigit():
                try:
                    order = Order.objects.get(id=int(order_id))
                    logger.info(f"Found order by ID: {order.id} (Number: {order.order_number})")
                except Order.DoesNotExist:
                    logger.warning(f"Order not found by ID: {order_id}")
                    return Response(
                        {'error': f'Order with ID {order_id} not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                try:
                    order = Order.objects.get(order_number=order_id)
                    logger.info(f"Found order by number: {order.order_number} (ID: {order.id})")
                except Order.DoesNotExist:
                    logger.warning(f"Order not found by order_number: {order_id}")
                    return Response(
                        {'error': f'Order with number {order_id} not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
        except Exception as e:
            logger.error(f"Unexpected error finding order: {e}", exc_info=True)
            return Response(
                {'error': 'An unexpected error occurred while finding the order'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check if order is already assigned
        try:
            if hasattr(order, 'delivery_assignment') and order.delivery_assignment:
                logger.warning(f"Order {order.order_number} is already assigned to rider {order.delivery_assignment.rider.name if order.delivery_assignment.rider else 'Unknown'}")
                return Response(
                    {'error': 'Order is already assigned to a rider'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error checking delivery assignment for order {order.order_number}: {e}", exc_info=True)

        # Prevent assignment of regular riders to Bolt orders
        if order.delivery_location and order.delivery_location.name == "Bolt Delivery":
            return Response(
                {'error': 'Cannot assign regular riders to Bolt delivery orders.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate order is ready for delivery
        if order.delivery_type != 'Delivery':
            logger.warning(f"Order {order.order_number} is not a delivery order (Type: {order.delivery_type})")
            return Response(
                {'error': f'Order is not a delivery order (Type: {order.delivery_type})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use the status constants from Order model
        if order.status not in [Order.STATUS_ACCEPTED, Order.STATUS_READY, Order.STATUS_OUT_FOR_DELIVERY]:
            logger.warning(f"Order {order.order_number} is not ready for delivery (Status: {order.status})")
            return Response(
                {'error': f'Order is not ready for delivery assignment (Status: {order.status}). Order must be in Accepted, Ready, or Out for Delivery status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AssignRiderSerializer(data=request.data)
        if serializer.is_valid():
            try:
                rider = DeliveryRider.objects.get(id=serializer.validated_data['rider_id'])
            except DeliveryRider.DoesNotExist:
                logger.error(f"Rider not found with ID: {serializer.validated_data['rider_id']}")
                return Response(
                    {'error': 'Selected rider not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            try:
                with transaction.atomic():
                    # Double-check that order doesn't have an assignment (in case of race condition)
                    if OrderAssignment.objects.filter(order=order).exists():
                        logger.error(f"Race condition: Order {order.order_number} was assigned while processing")
                        return Response(
                            {'error': 'Order was already assigned to another rider'},
                            status=status.HTTP_409_CONFLICT
                        )
                    
                    # Log current order state
                    logger.info(f"Creating assignment for order {order.order_number} (ID: {order.id}, Status: {order.status})")
                    logger.info(f"Assigning to rider {rider.name} (ID: {rider.id}, Available: {rider.is_available}, Current orders: {rider.current_orders})")
                    
                    # Create assignment
                    assignment = OrderAssignment.objects.create(
                        order=order,
                        rider=rider,
                        delivery_instructions=serializer.validated_data.get('delivery_instructions', ''),
                        picked_up_at=timezone.now()  # Set picked_up_at when order is assigned
                    )
                    logger.info(f"Assignment created with ID: {assignment.id}")
                    
                    # Update order status with proper status constant
                    order.status = Order.STATUS_OUT_FOR_DELIVERY  # Use the constant instead of string
                    order.save(update_fields=['status', 'updated_at'])
                    logger.info(f"Order {order.order_number} status updated to {order.status}")
                    
                    # Rider stats will be updated by signal
                    
                    # Serialize the response
                    response_data = OrderAssignmentSerializer(assignment).data
                    logger.info(f"Assignment successful for order {order.order_number}")
                    
                    return Response(
                        response_data,
                        status=status.HTTP_201_CREATED
                    )
            except IntegrityError as e:
                logger.error(f"Database integrity error creating assignment for order {order.order_number}: {e}", exc_info=True)
                return Response(
                    {'error': 'Order is already assigned or database constraint violated'},
                    status=status.HTTP_409_CONFLICT
                )
            except Exception as e:
                logger.error(f"Unexpected error creating assignment for order {order.order_number}: {e}", exc_info=True)
                logger.error(f"Error type: {type(e).__name__}")
                return Response(
                    {'error': f'Failed to create assignment: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        logger.warning(f"Invalid serializer data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeliveryLocationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing delivery locations and their fees"""
    queryset = DeliveryLocation.objects.all()
    serializer_class = DeliveryLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status if requested
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active delivery locations"""
        active_locations = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_locations, many=True)
        return Response(serializer.data)


class PublicDeliveryTrackingView(viewsets.ViewSet):
    """Public view for tracking deliveries"""
    permission_classes = []  # No authentication required
    
    def retrieve(self, request, order_number):
        """Track delivery by order number"""
        try:
            order = Order.objects.get(order_number=order_number)
            if not hasattr(order, 'delivery_assignment'):
                return Response(
                    {'error': 'No delivery information available for this order'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            assignment = order.delivery_assignment
            
            # Get public tracking info
            tracking_data = {
                'order_number': order.order_number,
                'status': assignment.get_status_display(),
                'rider_name': assignment.rider.name if assignment.rider else 'Not assigned',
                'estimated_delivery': None,  # TODO: Implement estimation logic
                'last_update': assignment.updated_at.isoformat() if hasattr(assignment, 'updated_at') else None
            }
            
            # Only show rider phone if order is out for delivery
            if assignment.status in ['picked_up', 'in_transit']:
                tracking_data['rider_phone'] = assignment.rider.phone if assignment.rider else None
            
            return Response(tracking_data)
            
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
