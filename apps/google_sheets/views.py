import logging
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers

from django.conf import settings
from django.utils import timezone

from apps.orders.models import Order
from apps.users.permissions import IsAdminOrFrontdesk
from .google_client_shared import get_google_sheets_client_shared as get_google_sheets_client
from .signals import prepare_order_data

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Get Google Sheets URL",
    description="Returns the URL of the master Google Sheets spreadsheet and today's sheet",
    responses={
        200: inline_serializer(
            name='GoogleSheetsURLResponse',
            fields={
                'master_spreadsheet_url': serializers.CharField(),
                'today_sheet_url': serializers.CharField(),
                'spreadsheet_id': serializers.CharField(),
                'sync_enabled': serializers.BooleanField(),
            }
        ),
        503: inline_serializer(
            name='GoogleSheetsError',
            fields={
                'error': serializers.CharField(),
                'sync_enabled': serializers.BooleanField(),
            }
        )
    },
    tags=['Google Sheets']
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_sheets_url(request):
    """Get the URL of the Google Sheets spreadsheet."""
    sync_enabled = getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', False)
    
    if not sync_enabled:
        return Response(
            {
                'error': 'Google Sheets sync is not enabled',
                'sync_enabled': False
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        client = get_google_sheets_client()
        return Response({
            'master_spreadsheet_url': client.get_spreadsheet_url(),
            'today_sheet_url': client.get_daily_sheet_url(),
            'spreadsheet_id': client.spreadsheet_id,
            'sync_enabled': True
        })
    except Exception as e:
        logger.error(f"Error getting Google Sheets URL: {e}")
        return Response(
            {
                'error': f'Failed to get Google Sheets URL: {str(e)}',
                'sync_enabled': True
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@extend_schema(
    summary="Sync Order to Google Sheets",
    description="Manually sync a specific order to Google Sheets",
    parameters=[
        OpenApiParameter(
            name='order_number',
            description='Order number to sync',
            required=True,
            type=str
        ),
    ],
    responses={
        200: inline_serializer(
            name='SyncOrderResponse',
            fields={
                'message': serializers.CharField(),
                'order_number': serializers.CharField(),
                'sheet_url': serializers.CharField(),
            }
        ),
        404: inline_serializer(
            name='OrderNotFound',
            fields={
                'error': serializers.CharField(),
            }
        )
    },
    tags=['Google Sheets']
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminOrFrontdesk])
def sync_order(request, order_number):
    """Manually sync a specific order to Google Sheets."""
    if not getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', False):
        return Response(
            {'error': 'Google Sheets sync is not enabled'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response(
            {'error': f'Order {order_number} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        client = get_google_sheets_client()
        order_data = prepare_order_data(order)
        
        # Try to update first, if not found, add new
        success = client.update_order_in_sheet(order_number, order_data)
        if not success:
            success = client.add_order_to_sheet(order_data)
        
        if success:
            sheet_url = client.get_daily_sheet_url(order.created_at)
            return Response({
                'message': f'Order {order_number} synced successfully',
                'order_number': order_number,
                'sheet_url': sheet_url
            })
        else:
            return Response(
                {'error': f'Failed to sync order {order_number}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        logger.error(f"Error syncing order {order_number}: {e}")
        return Response(
            {'error': f'Error syncing order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Bulk Sync Orders to Google Sheets",
    description="Sync multiple orders to Google Sheets for a specific date range",
    parameters=[
        OpenApiParameter(
            name='start_date',
            description='Start date (YYYY-MM-DD)',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='end_date',
            description='End date (YYYY-MM-DD)',
            required=False,
            type=str
        ),
    ],
    responses={
        200: inline_serializer(
            name='BulkSyncResponse',
            fields={
                'message': serializers.CharField(),
                'orders_synced': serializers.IntegerField(),
                'orders_failed': serializers.IntegerField(),
                'failed_orders': serializers.ListField(child=serializers.CharField()),
            }
        )
    },
    tags=['Google Sheets']
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminOrFrontdesk])
def bulk_sync_orders(request):
    """Bulk sync orders to Google Sheets."""
    if not getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', False):
        return Response(
            {'error': 'Google Sheets sync is not enabled'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Parse date parameters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Default to today if no dates provided
    if not start_date:
        start_date = timezone.now().date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = start_date
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get orders in date range
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).order_by('created_at')
    
    synced_count = 0
    failed_count = 0
    failed_orders = []
    
    try:
        client = get_google_sheets_client()
        
        for order in orders:
            try:
                order_data = prepare_order_data(order)
                
                # Set the current user for audit
                order._current_user = request.user
                
                # Try to update first, if not found, add new
                success = client.update_order_in_sheet(order.order_number, order_data)
                if not success:
                    success = client.add_order_to_sheet(order_data)
                
                if success:
                    synced_count += 1
                else:
                    failed_count += 1
                    failed_orders.append(order.order_number)
                    
            except Exception as e:
                logger.error(f"Error syncing order {order.order_number}: {e}")
                failed_count += 1
                failed_orders.append(order.order_number)
        
        return Response({
            'message': f'Bulk sync completed for {start_date} to {end_date}',
            'orders_synced': synced_count,
            'orders_failed': failed_count,
            'failed_orders': failed_orders
        })
        
    except Exception as e:
        logger.error(f"Error in bulk sync: {e}")
        return Response(
            {'error': f'Bulk sync failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Test Google Sheets Connection",
    description="Test the connection to Google Sheets and verify credentials",
    responses={
        200: inline_serializer(
            name='TestConnectionResponse',
            fields={
                'status': serializers.CharField(),
                'spreadsheet_id': serializers.CharField(),
                'spreadsheet_url': serializers.CharField(),
                'worksheet_count': serializers.IntegerField(),
                'today_sheet_exists': serializers.BooleanField(),
            }
        ),
        503: inline_serializer(
            name='ConnectionError',
            fields={
                'status': serializers.CharField(),
                'error': serializers.CharField(),
            }
        )
    },
    tags=['Google Sheets']
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminOrFrontdesk])
def test_connection(request):
    """Test the Google Sheets connection."""
    if not getattr(settings, 'GOOGLE_SHEETS_SYNC_ENABLED', False):
        return Response(
            {
                'status': 'disabled',
                'error': 'Google Sheets sync is not enabled'
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        client = get_google_sheets_client()
        
        # Test by getting spreadsheet info
        spreadsheet = client.client.open_by_key(client.spreadsheet_id)
        worksheet_count = len(spreadsheet.worksheets())
        
        # Check if today's sheet exists
        today_name = datetime.now().strftime("%Y-%m-%d")
        today_exists = any(ws.title == today_name for ws in spreadsheet.worksheets())
        
        return Response({
            'status': 'connected',
            'spreadsheet_id': client.spreadsheet_id,
            'spreadsheet_url': client.get_spreadsheet_url(),
            'worksheet_count': worksheet_count,
            'today_sheet_exists': today_exists,
        })
        
    except Exception as e:
        logger.error(f"Google Sheets connection test failed: {e}")
        return Response(
            {
                'status': 'error',
                'error': str(e)
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
