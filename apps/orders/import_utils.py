import csv
import json
import io
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Order, OrderItem
from apps.menu.models import MenuItem
from apps.deliveries.models import DeliveryLocation


class OrderImporter:
    """Handles importing orders from various formats"""
    
    def __init__(self, user=None):
        self.user = user
        self.errors = []
        self.warnings = []
        self.imported_count = 0
        self.skipped_count = 0
    
    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse datetime from various formats"""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
            '%m/%d/%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_str}")
    
    def _find_or_create_delivery_location(self, location_name: str) -> Optional[DeliveryLocation]:
        """Find or create a delivery location"""
        if not location_name or location_name.lower() in ['n/a', 'none', '']:
            return None
        
        try:
            return DeliveryLocation.objects.get(name__iexact=location_name)
        except DeliveryLocation.DoesNotExist:
            # Create a new delivery location with default fee
            return DeliveryLocation.objects.create(
                name=location_name,
                fee=Decimal('0.00'),
                is_active=True
            )
    
    def _find_menu_item(self, item_name: str) -> Optional[MenuItem]:
        """Find a menu item by name"""
        try:
            return MenuItem.objects.get(name__iexact=item_name, is_available=True)
        except MenuItem.DoesNotExist:
            return None
        except MenuItem.MultipleObjectsReturned:
            # If multiple items with same name, take the first active one
            return MenuItem.objects.filter(name__iexact=item_name, is_available=True).first()
    
    def _parse_items_string(self, items_str: str) -> List[Dict[str, Any]]:
        """Parse items from a string format like '2x Item1 @ 10.00; 3x Item2 @ 15.00'"""
        items = []
        
        if not items_str:
            return items
        
        # Split by semicolon
        item_parts = items_str.split(';')
        
        for part in item_parts:
            part = part.strip()
            if not part:
                continue
            
            try:
                # Parse format: "2x Item Name @ 10.00"
                if 'x' in part and '@' in part:
                    qty_part, rest = part.split('x', 1)
                    name_part, price_part = rest.split('@', 1)
                    
                    quantity = int(qty_part.strip())
                    item_name = name_part.strip()
                    unit_price = Decimal(price_part.strip())
                    
                    items.append({
                        'name': item_name,
                        'quantity': quantity,
                        'unit_price': unit_price
                    })
            except Exception as e:
                self.warnings.append(f"Could not parse item: {part}")
        
        return items
    
    def import_from_csv(self, file_content: str) -> Tuple[int, List[str], List[str]]:
        """Import orders from CSV content"""
        self.errors = []
        self.warnings = []
        self.imported_count = 0
        self.skipped_count = 0
        
        reader = csv.DictReader(io.StringIO(file_content))
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    # Check if order already exists
                    order_number = row.get('Order Number', '').strip()
                    if order_number and Order.objects.filter(order_number=order_number).exists():
                        self.warnings.append(f"Row {row_num}: Order {order_number} already exists, skipping")
                        self.skipped_count += 1
                        continue
                    
                    # Parse delivery location
                    delivery_location = None
                    location_name = row.get('Delivery Location', '').strip()
                    if location_name and location_name.lower() not in ['n/a', 'none', '']:
                        delivery_location = self._find_or_create_delivery_location(location_name)
                    
                    # Create order
                    order = Order(
                        customer_phone=row.get('Customer Phone', '').strip() or None,
                        delivery_type=row.get('Delivery Type', 'Pickup').strip(),
                        delivery_location=delivery_location,
                        status=row.get('Status', Order.STATUS_PENDING).strip(),
                        notes=row.get('Notes', '').strip()
                    )
                    
                    # Handle custom order number if provided
                    if order_number:
                        order.order_number = order_number
                    
                    # Set delivery fee
                    delivery_fee_str = row.get('Delivery Fee', '0').strip()
                    try:
                        order.delivery_fee = Decimal(delivery_fee_str)
                    except:
                        order.delivery_fee = Decimal('0.00')
                    
                    order.full_clean()
                    order.save()
                    
                    # Parse and create order items
                    items_str = row.get('Items', '').strip()
                    items_data = self._parse_items_string(items_str)
                    
                    for item_data in items_data:
                        menu_item = self._find_menu_item(item_data['name'])
                        
                        order_item = OrderItem(
                            order=order,
                            menu_item=menu_item,
                            item_name=item_data['name'] if not menu_item else '',
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price'] if not menu_item else menu_item.price
                        )
                        order_item.save()
                    
                    # Recalculate order total
                    order.calculate_total()
                    order.save()
                    
                    self.imported_count += 1
                    
                except Exception as e:
                    self.errors.append(f"Row {row_num}: {str(e)}")
                    raise  # Re-raise to trigger rollback
        
        return self.imported_count, self.errors, self.warnings
    
    def import_from_excel(self, file_content: bytes) -> Tuple[int, List[str], List[str]]:
        """Import orders from Excel content"""
        self.errors = []
        self.warnings = []
        self.imported_count = 0
        self.skipped_count = 0
        
        try:
            df = pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            self.errors.append(f"Failed to read Excel file: {str(e)}")
            return 0, self.errors, self.warnings
        
        with transaction.atomic():
            for idx, row in df.iterrows():
                row_num = idx + 2  # Excel rows start at 1, header at 1, data at 2
                try:
                    # Check if order already exists
                    order_number = str(row.get('Order Number', '')).strip()
                    if order_number and Order.objects.filter(order_number=order_number).exists():
                        self.warnings.append(f"Row {row_num}: Order {order_number} already exists, skipping")
                        self.skipped_count += 1
                        continue
                    
                    # Parse delivery location
                    delivery_location = None
                    location_name = str(row.get('Delivery Location', '')).strip()
                    if location_name and location_name.lower() not in ['n/a', 'none', 'nan', '']:
                        delivery_location = self._find_or_create_delivery_location(location_name)
                    
                    # Create order
                    customer_phone = str(row.get('Customer Phone', '')).strip()
                    if customer_phone.lower() in ['n/a', 'none', 'nan']:
                        customer_phone = None
                    
                    order = Order(
                        customer_phone=customer_phone,
                        delivery_type=str(row.get('Delivery Type', 'Pickup')).strip(),
                        delivery_location=delivery_location,
                        status=str(row.get('Status', Order.STATUS_PENDING)).strip(),
                        notes=str(row.get('Notes', '')).strip()
                    )
                    
                    # Handle custom order number if provided
                    if order_number and order_number.lower() not in ['nan', '']:
                        order.order_number = order_number
                    
                    # Set delivery fee
                    try:
                        order.delivery_fee = Decimal(str(row.get('Delivery Fee', 0)))
                    except:
                        order.delivery_fee = Decimal('0.00')
                    
                    order.full_clean()
                    order.save()
                    
                    # Check for individual item columns
                    item_count = 1
                    while f'Item {item_count} Name' in row:
                        item_name = str(row.get(f'Item {item_count} Name', '')).strip()
                        if item_name and item_name.lower() not in ['nan', '']:
                            try:
                                quantity = int(row.get(f'Item {item_count} Qty', 1))
                                unit_price = Decimal(str(row.get(f'Item {item_count} Price', 0)))
                                
                                menu_item = self._find_menu_item(item_name)
                                
                                order_item = OrderItem(
                                    order=order,
                                    menu_item=menu_item,
                                    item_name=item_name if not menu_item else '',
                                    quantity=quantity,
                                    unit_price=unit_price if not menu_item else menu_item.price
                                )
                                order_item.save()
                            except Exception as e:
                                self.warnings.append(f"Row {row_num}, Item {item_count}: {str(e)}")
                        
                        item_count += 1
                    
                    # If no individual items found, try parsing Items column
                    if item_count == 1:
                        items_str = str(row.get('Items', '')).strip()
                        if items_str and items_str.lower() not in ['nan', '']:
                            items_data = self._parse_items_string(items_str)
                            
                            for item_data in items_data:
                                menu_item = self._find_menu_item(item_data['name'])
                                
                                order_item = OrderItem(
                                    order=order,
                                    menu_item=menu_item,
                                    item_name=item_data['name'] if not menu_item else '',
                                    quantity=item_data['quantity'],
                                    unit_price=item_data['unit_price'] if not menu_item else menu_item.price
                                )
                                order_item.save()
                    
                    # Recalculate order total
                    order.calculate_total()
                    order.save()
                    
                    self.imported_count += 1
                    
                except Exception as e:
                    self.errors.append(f"Row {row_num}: {str(e)}")
                    raise  # Re-raise to trigger rollback
        
        return self.imported_count, self.errors, self.warnings
    
    def import_from_json(self, file_content: str) -> Tuple[int, List[str], List[str]]:
        """Import orders from JSON content"""
        self.errors = []
        self.warnings = []
        self.imported_count = 0
        self.skipped_count = 0
        
        try:
            data = json.loads(file_content)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON format: {str(e)}")
            return 0, self.errors, self.warnings
        
        # Handle both raw array and wrapped format
        if isinstance(data, list):
            orders_data = data
        elif isinstance(data, dict) and 'orders' in data:
            orders_data = data['orders']
        else:
            self.errors.append("Invalid JSON structure. Expected array of orders or object with 'orders' key.")
            return 0, self.errors, self.warnings
        
        with transaction.atomic():
            for idx, order_data in enumerate(orders_data):
                try:
                    # Check if order already exists
                    order_number = order_data.get('order_number', '').strip()
                    if order_number and Order.objects.filter(order_number=order_number).exists():
                        self.warnings.append(f"Order {order_number} already exists, skipping")
                        self.skipped_count += 1
                        continue
                    
                    # Parse delivery location
                    delivery_location = None
                    location_name = order_data.get('delivery_location', '').strip()
                    if location_name:
                        delivery_location = self._find_or_create_delivery_location(location_name)
                    
                    # Create order
                    order = Order(
                        customer_phone=order_data.get('customer_phone'),
                        delivery_type=order_data.get('delivery_type', 'Pickup'),
                        delivery_location=delivery_location,
                        status=order_data.get('status', Order.STATUS_PENDING),
                        notes=order_data.get('notes', '')
                    )
                    
                    # Handle custom order number if provided
                    if order_number:
                        order.order_number = order_number
                    
                    # Set delivery fee
                    order.delivery_fee = Decimal(str(order_data.get('delivery_fee', 0)))
                    
                    order.full_clean()
                    order.save()
                    
                    # Create order items
                    items_data = order_data.get('items', [])
                    for item_data in items_data:
                        menu_item_id = item_data.get('menu_item_id')
                        menu_item = None
                        
                        if menu_item_id:
                            try:
                                menu_item = MenuItem.objects.get(id=menu_item_id)
                            except MenuItem.DoesNotExist:
                                item_name = item_data.get('menu_item_name', '')
                                if item_name:
                                    menu_item = self._find_menu_item(item_name)
                        
                        order_item = OrderItem(
                            order=order,
                            menu_item=menu_item,
                            item_name=item_data.get('menu_item_name', '') if not menu_item else '',
                            quantity=item_data.get('quantity', 1),
                            unit_price=Decimal(str(item_data.get('unit_price', 0))),
                            notes=item_data.get('notes', '')
                        )
                        order_item.save()
                    
                    # Recalculate order total
                    order.calculate_total()
                    order.save()
                    
                    self.imported_count += 1
                    
                except Exception as e:
                    self.errors.append(f"Order {idx + 1}: {str(e)}")
                    raise  # Re-raise to trigger rollback
        
        return self.imported_count, self.errors, self.warnings
