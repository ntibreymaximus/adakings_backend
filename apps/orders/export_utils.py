import csv
import json
import io
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from django.http import HttpResponse
from django.db.models import QuerySet
from .models import Order, OrderItem
from .serializers import OrderSerializer


class OrderExporter:
    """Handles exporting orders to various formats"""
    
    @staticmethod
    def export_to_csv(orders: QuerySet[Order]) -> HttpResponse:
        """Export orders to CSV format"""
        response = HttpResponse(content_type='text/csv')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="orders_{timestamp}.csv"'
        
        writer = csv.writer(response)
        
        # Headers
        headers = [
            'Order Number', 'Order Date', 'Customer Phone', 'Delivery Type',
            'Delivery Location', 'Status', 'Payment Status', 'Items', 
            'Subtotal', 'Delivery Fee', 'Total Price', 'Amount Paid', 
            'Balance Due', 'Notes'
        ]
        writer.writerow(headers)
        
        # Data rows
        for order in orders.select_related('delivery_location').prefetch_related('items__menu_item'):
            items_str = '; '.join([
                f"{item.quantity}x {item.item_name or (item.menu_item.name if item.menu_item else 'Unknown')} @ {item.unit_price}"
                for item in order.items.all()
            ])
            
            row = [
                order.order_number,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                order.customer_phone or 'N/A',
                order.delivery_type,
                order.get_effective_delivery_location_name() or 'N/A',
                order.status,
                order.get_payment_status(),
                items_str,
                order.total_price - order.delivery_fee,  # Subtotal
                order.delivery_fee,
                order.total_price,
                order.amount_paid(),
                order.balance_due(),
                order.notes
            ]
            writer.writerow(row)
        
        return response
    
    @staticmethod
    def export_to_excel(orders: QuerySet[Order]) -> HttpResponse:
        """Export orders to Excel format"""
        # Create a DataFrame
        data = []
        
        for order in orders.select_related('delivery_location').prefetch_related('items__menu_item', 'payments'):
            # Basic order data
            order_data = {
                'Order Number': order.order_number,
                'Order Date': order.created_at,
                'Customer Phone': order.customer_phone or 'N/A',
                'Delivery Type': order.delivery_type,
                'Delivery Location': order.get_effective_delivery_location_name() or 'N/A',
                'Status': order.status,
                'Payment Status': order.get_payment_status(),
                'Subtotal': float(order.total_price - order.delivery_fee),
                'Delivery Fee': float(order.delivery_fee),
                'Total Price': float(order.total_price),
                'Amount Paid': float(order.amount_paid()),
                'Balance Due': float(order.balance_due()),
                'Notes': order.notes
            }
            
            # Add item details
            for idx, item in enumerate(order.items.all(), 1):
                order_data[f'Item {idx} Name'] = item.item_name or (item.menu_item.name if item.menu_item else 'Unknown')
                order_data[f'Item {idx} Qty'] = item.quantity
                order_data[f'Item {idx} Price'] = float(item.unit_price)
                order_data[f'Item {idx} Subtotal'] = float(item.subtotal)
            
            data.append(order_data)
        
        df = pd.DataFrame(data)
        
        # Create Excel file
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="orders_{timestamp}.xlsx"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Orders', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Orders']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)
        
        return response
    
    @staticmethod
    def export_to_json(orders: QuerySet[Order]) -> HttpResponse:
        """Export orders to JSON format"""
        serializer = OrderSerializer(orders, many=True)
        
        response = HttpResponse(content_type='application/json')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="orders_{timestamp}.json"'
        
        json_data = {
            'export_date': datetime.now().isoformat(),
            'total_orders': orders.count(),
            'orders': serializer.data
        }
        
        response.write(json.dumps(json_data, indent=2, default=str))
        return response
    
    @staticmethod
    def export_to_pdf(orders: QuerySet[Order]) -> HttpResponse:
        """Export orders to PDF format"""
        response = HttpResponse(content_type='application/pdf')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="orders_{timestamp}.pdf"'
        
        # Create the PDF object
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#333333'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#444444'),
            spaceAfter=12
        )
        
        # Title
        elements.append(Paragraph("Orders Report", title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Summary statistics
        total_revenue = sum(order.total_price for order in orders)
        total_paid = sum(order.amount_paid() for order in orders)
        total_due = sum(order.balance_due() for order in orders)
        
        summary_data = [
            ['Summary Statistics', ''],
            ['Total Orders:', str(orders.count())],
            ['Total Revenue:', f'GH₵ {total_revenue:,.2f}'],
            ['Total Paid:', f'GH₵ {total_paid:,.2f}'],
            ['Total Due:', f'GH₵ {total_due:,.2f}'],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Orders detail
        elements.append(Paragraph("Order Details", heading_style))
        
        for order in orders.select_related('delivery_location').prefetch_related('items__menu_item'):
            # Order header
            order_data = [
                ['Order #', order.order_number, 'Date', order.created_at.strftime('%Y-%m-%d %H:%M')],
                ['Customer', order.customer_phone or 'Walk-in', 'Status', order.status],
                ['Delivery', order.delivery_type, 'Location', order.get_effective_delivery_location_name() or 'N/A'],
                ['Payment Status', order.get_payment_status(), 'Total', f'GH₵ {order.total_price:,.2f}'],
            ]
            
            order_table = Table(order_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
            order_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            
            elements.append(order_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Order items
            if order.items.exists():
                items_data = [['Item', 'Qty', 'Unit Price', 'Subtotal']]
                for item in order.items.all():
                    item_name = item.item_name or (item.menu_item.name if item.menu_item else 'Unknown')
                    items_data.append([
                        item_name,
                        str(item.quantity),
                        f'GH₵ {item.unit_price:,.2f}',
                        f'GH₵ {item.subtotal:,.2f}'
                    ])
                
                # Add delivery fee if applicable
                if order.delivery_fee > 0:
                    items_data.append(['Delivery Fee', '', '', f'GH₵ {order.delivery_fee:,.2f}'])
                
                items_table = Table(items_data, colWidths=[3.5*inch, 1*inch, 1.5*inch, 1.5*inch])
                items_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ]))
                
                elements.append(items_table)
            
            elements.append(Spacer(1, 0.4*inch))
        
        # Build PDF
        doc.build(elements)
        return response
