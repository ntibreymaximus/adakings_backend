import json
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer
from rest_framework import serializers

from .models import Order
from .export_utils import OrderExporter
from .import_utils import OrderImporter
from apps.users.permissions import IsAdminOrFrontdesk
from apps.audit.utils import log_create


@extend_schema(
    summary="Export Orders",
    description="Export orders to various formats (CSV, Excel, JSON, PDF). Supports filtering by date range and status.",
    parameters=[
        OpenApiParameter(
            name='format',
            description='Export format (csv, excel, json, pdf)',
            required=True,
            type=OpenApiTypes.STR,
            enum=['csv', 'excel', 'json', 'pdf']
        ),
        OpenApiParameter(
            name='start_date',
            description='Start date for filtering (YYYY-MM-DD)',
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name='end_date',
            description='End date for filtering (YYYY-MM-DD)',
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name='status',
            description='Filter by order status',
            required=False,
            type=OpenApiTypes.STR,
            enum=['Pending', 'Accepted', 'Ready', 'Out for Delivery', 'Fulfilled', 'Cancelled']
        ),
        OpenApiParameter(
            name='delivery_type',
            description='Filter by delivery type',
            required=False,
            type=OpenApiTypes.STR,
            enum=['Pickup', 'Delivery']
        ),
    ],
    responses={
        200: inline_serializer(
            name='ExportResponse',
            fields={
                'file': serializers.FileField(help_text='The exported file')
            }
        ),
        400: inline_serializer(
            name='ExportError',
            fields={
                'error': serializers.CharField()
            }
        )
    },
    tags=['Orders Export/Import']
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminOrFrontdesk])
def export_orders(request):
    """Export orders to various formats"""
    # Get export format
    export_format = request.query_params.get('format', '').lower()
    if export_format not in ['csv', 'excel', 'json', 'pdf']:
        return Response(
            {'error': 'Invalid format. Must be one of: csv, excel, json, pdf'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Build queryset with filters
    queryset = Order.objects.all()
    
    # Date filtering
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        try:
            start_datetime = timezone.datetime.strptime(start_date, '%Y-%m-%d')
            queryset = queryset.filter(created_at__gte=start_datetime)
        except ValueError:
            return Response({'error': 'Invalid start_date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
    
    if end_date:
        try:
            end_datetime = timezone.datetime.strptime(end_date, '%Y-%m-%d')
            # Add 1 day to include the entire end date
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            queryset = queryset.filter(created_at__lte=end_datetime)
        except ValueError:
            return Response({'error': 'Invalid end_date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Status filtering
    order_status = request.query_params.get('status')
    if order_status:
        queryset = queryset.filter(status=order_status)
    
    # Delivery type filtering
    delivery_type = request.query_params.get('delivery_type')
    if delivery_type:
        queryset = queryset.filter(delivery_type=delivery_type)
    
    # Order by created_at
    queryset = queryset.order_by('-created_at')
    
    # Export based on format
    exporter = OrderExporter()
    
    try:
        if export_format == 'csv':
            return exporter.export_to_csv(queryset)
        elif export_format == 'excel':
            return exporter.export_to_excel(queryset)
        elif export_format == 'json':
            return exporter.export_to_json(queryset)
        elif export_format == 'pdf':
            return exporter.export_to_pdf(queryset)
    except Exception as e:
        return Response(
            {'error': f'Export failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Import Orders",
    description="Import orders from CSV, Excel, or JSON files. Duplicate orders (by order number) will be skipped.",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'The file to import (CSV, Excel, or JSON)'
                },
                'format': {
                    'type': 'string',
                    'enum': ['csv', 'excel', 'json'],
                    'description': 'The format of the file being imported'
                }
            },
            'required': ['file', 'format']
        }
    },
    responses={
        200: inline_serializer(
            name='ImportSuccess',
            fields={
                'message': serializers.CharField(),
                'imported': serializers.IntegerField(),
                'skipped': serializers.IntegerField(),
                'warnings': serializers.ListField(child=serializers.CharField()),
            }
        ),
        400: inline_serializer(
            name='ImportError',
            fields={
                'error': serializers.CharField(),
                'details': serializers.ListField(child=serializers.CharField(), required=False),
            }
        )
    },
    tags=['Orders Export/Import']
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminOrFrontdesk])
def import_orders(request):
    """Import orders from uploaded file"""
    # Check if file is provided
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get file and format
    uploaded_file = request.FILES['file']
    file_format = request.data.get('format', '').lower()
    
    if file_format not in ['csv', 'excel', 'json']:
        return Response(
            {'error': 'Invalid format. Must be one of: csv, excel, json'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Initialize importer
    importer = OrderImporter(user=request.user)
    
    try:
        # Read file content
        if file_format in ['csv', 'json']:
            file_content = uploaded_file.read().decode('utf-8')
        else:  # excel
            file_content = uploaded_file.read()
        
        # Import based on format
        if file_format == 'csv':
            imported, errors, warnings = importer.import_from_csv(file_content)
        elif file_format == 'excel':
            imported, errors, warnings = importer.import_from_excel(file_content)
        elif file_format == 'json':
            imported, errors, warnings = importer.import_from_json(file_content)
        
        # Check for errors
        if errors:
            return Response(
                {
                    'error': 'Import failed with errors',
                    'details': errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log the import
        log_create(
            user=request.user,
            obj=None,  # No specific object, this is a bulk operation
            request=request,
            extra_data={
                'description': f'Imported {imported} orders from {file_format.upper()} file',
                'filename': uploaded_file.name,
                'imported_count': imported,
                'skipped_count': importer.skipped_count,
                'warnings_count': len(warnings)
            }
        )
        
        # Return success response
        response_data = {
            'message': f'Successfully imported {imported} orders',
            'imported': imported,
            'skipped': importer.skipped_count,
            'warnings': warnings
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': f'Import failed: {str(e)}',
                'details': [str(e)]
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Download Import Template",
    description="Download a template file for importing orders in the specified format",
    parameters=[
        OpenApiParameter(
            name='format',
            description='Template format (csv, excel, json)',
            required=True,
            type=OpenApiTypes.STR,
            enum=['csv', 'excel', 'json']
        ),
    ],
    responses={
        200: inline_serializer(
            name='TemplateResponse',
            fields={
                'file': serializers.FileField(help_text='The template file')
            }
        ),
        400: inline_serializer(
            name='TemplateError',
            fields={
                'error': serializers.CharField()
            }
        )
    },
    tags=['Orders Export/Import']
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminOrFrontdesk])
def download_import_template(request):
    """Download a template for importing orders"""
    template_format = request.query_params.get('format', '').lower()
    
    if template_format not in ['csv', 'excel', 'json']:
        return Response(
            {'error': 'Invalid format. Must be one of: csv, excel, json'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create sample data
    sample_data = [
        {
            'Order Number': '161124-001',  # Optional, will be auto-generated if empty
            'Customer Phone': '+233244123456',
            'Delivery Type': 'Delivery',
            'Delivery Location': 'Accra Mall',
            'Status': 'Pending',
            'Items': '2x Jollof Rice @ 25.00; 1x Grilled Chicken @ 35.00',
            'Delivery Fee': '10.00',
            'Notes': 'Please add extra pepper'
        },
        {
            'Order Number': '',  # Will be auto-generated
            'Customer Phone': '0201234567',
            'Delivery Type': 'Pickup',
            'Delivery Location': '',
            'Status': 'Pending',
            'Items': '1x Banku with Tilapia @ 40.00; 2x Coca Cola @ 5.00',
            'Delivery Fee': '0.00',
            'Notes': ''
        }
    ]
    
    if template_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="order_import_template.csv"'
        
        import csv
        writer = csv.DictWriter(response, fieldnames=sample_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_data)
        
        return response
        
    elif template_format == 'excel':
        import pandas as pd
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="order_import_template.xlsx"'
        
        df = pd.DataFrame(sample_data)
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Orders', index=False)
            
            # Add a second sheet with instructions
            instructions = pd.DataFrame({
                'Field': ['Order Number', 'Customer Phone', 'Delivery Type', 'Delivery Location', 'Status', 'Items', 'Delivery Fee', 'Notes'],
                'Description': [
                    'Optional. Format: DDMMYY-XXX. Will be auto-generated if empty.',
                    'Required for delivery orders. Format: +233XXXXXXXXX or 0XXXXXXXXX',
                    'Required. Must be either "Pickup" or "Delivery"',
                    'Required for delivery orders. Will create new location if not found.',
                    'Optional. Default is "Pending". Options: Pending, Accepted, Ready, Out for Delivery, Fulfilled, Cancelled',
                    'Required. Format: QuantityxItemName @ Price; ... Multiple items separated by semicolon',
                    'Optional. Default is 0.00',
                    'Optional. Any additional notes for the order'
                ],
                'Example': [
                    '161124-001',
                    '+233244123456',
                    'Delivery',
                    'Accra Mall',
                    'Pending',
                    '2x Jollof Rice @ 25.00; 1x Chicken @ 35.00',
                    '10.00',
                    'Extra pepper please'
                ]
            })
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
            
            # Auto-adjust column widths
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return response
        
    elif template_format == 'json':
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="order_import_template.json"'
        
        json_template = {
            "instructions": {
                "description": "Import orders using this JSON structure",
                "notes": [
                    "order_number is optional and will be auto-generated if not provided",
                    "customer_phone is required for delivery orders",
                    "delivery_location will be created if it doesn't exist",
                    "menu_item_id is preferred over menu_item_name for accuracy"
                ]
            },
            "orders": [
                {
                    "order_number": "161124-001",
                    "customer_phone": "+233244123456",
                    "delivery_type": "Delivery",
                    "delivery_location": "Accra Mall",
                    "status": "Pending",
                    "delivery_fee": 10.00,
                    "notes": "Please add extra pepper",
                    "items": [
                        {
                            "menu_item_name": "Jollof Rice",
                            "quantity": 2,
                            "unit_price": 25.00,
                            "notes": ""
                        },
                        {
                            "menu_item_name": "Grilled Chicken",
                            "quantity": 1,
                            "unit_price": 35.00,
                            "notes": ""
                        }
                    ]
                },
                {
                    "customer_phone": "0201234567",
                    "delivery_type": "Pickup",
                    "status": "Pending",
                    "delivery_fee": 0.00,
                    "notes": "",
                    "items": [
                        {
                            "menu_item_name": "Banku with Tilapia",
                            "quantity": 1,
                            "unit_price": 40.00
                        }
                    ]
                }
            ]
        }
        
        response.write(json.dumps(json_template, indent=2))
        return response
