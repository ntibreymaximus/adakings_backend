import os
import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.menu.models import MenuItem
from apps.core.db_utils import retry_on_db_lock

User = get_user_model()


class Command(BaseCommand):
    help = 'Load menu items from adakings_menu.txt file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='adakings_menu.txt',
            help='Path to the menu file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing menu items before loading new ones'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing menu items if they exist'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        update_existing = options['update']
        
        # Get absolute path
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return
        
        # Get or create system user
        system_user, _ = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@adakings.com',
                'is_staff': True,
                'is_active': True
            }
        )
        
        # Clear existing menu items if requested
        if clear_existing:
            # First, deactivate all existing items (don't delete to preserve order references)
            deactivated = MenuItem.objects.filter(is_available=True).update(is_available=False)
            self.stdout.write(self.style.WARNING(f"Deactivated {deactivated} existing menu items"))
            
            # Delete menu items that are not referenced in any orders
            # This is safe now because OrderItem uses SET_NULL
            unreferenced_items = MenuItem.objects.filter(
                is_available=False,
                order_items__isnull=True  # No order items reference this menu item
            )
            deleted_count = unreferenced_items.count()
            if deleted_count > 0:
                unreferenced_items.delete()
                self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} unreferenced menu items"))
        
        # Parse the file
        menu_data = self.parse_menu_file(file_path)
        
        # First, collect all valid items from the menu file
        valid_items = set()
        for category, items in menu_data.items():
            for item_name, item_price in items:
                item_name = item_name.strip()
                if not item_name:
                    continue
                
                # Determine item type based on category
                if category == 'EXTRA':
                    item_type = 'extra'
                elif category == 'BOLT':
                    item_type = 'bolt'
                    # Add BOLT- prefix if not already present
                    if not item_name.startswith('BOLT-'):
                        item_name = f'BOLT-{item_name}'
                else:  # REGULAR
                    item_type = 'regular'
                
                valid_items.add((item_name, item_type))
        
        # Remove items that are not in the menu file (always sync to match file exactly)
        self._remove_outdated_menu_items(valid_items)
        
        # Load menu items into database
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for category, items in menu_data.items():
            for item_name, item_price in items:
                item_name = item_name.strip()
                if not item_name:
                    continue
                
                # Determine item type based on category
                if category == 'EXTRA':
                    item_type = 'extra'
                elif category == 'BOLT':
                    item_type = 'bolt'
                    # Add BOLT- prefix if not already present
                    if not item_name.startswith('BOLT-'):
                        item_name = f'BOLT-{item_name}'
                else:  # REGULAR
                    item_type = 'regular'
                
                try:
                    result = self._process_menu_item(
                        item_name, item_price, item_type, system_user,
                        update_existing, clear_existing, valid_items
                    )
                    if result == 'created':
                        created_count += 1
                    elif result == 'updated':
                        updated_count += 1
                    elif result == 'skipped':
                        skipped_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing {item_name}: {str(e)}"))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\nSummary:\n"
            f"  Created: {created_count} items\n"
            f"  Updated: {updated_count} items\n"
            f"  Skipped: {skipped_count} items\n"
            f"  Total in database: {MenuItem.objects.count()} items"
        ))
        
        # Show all available items grouped by type
        self.stdout.write("\nCurrent available menu items by type:")
        for item_type in ['regular', 'extra', 'bolt']:
            type_label = 'REGULAR' if item_type == 'regular' else item_type.upper()
            items = MenuItem.objects.filter(item_type=item_type, is_available=True).order_by('name')
            if items.exists():
                self.stdout.write(f"\n{{{type_label}}}:")
                for item in items:
                    self.stdout.write(f"  {item.name} - ₵{item.price:.2f}")
    
    def parse_menu_file(self, file_path):
        """Parse the menu file and return a dictionary of {category: [(name, price)]}"""
        menu_data = {}
        current_category = None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if not line:
                    continue
                
                # Check if this is a category line
                category_match = re.match(r'\{(\w+)\}', line)
                if category_match:
                    current_category = category_match.group(1)
                    if current_category not in menu_data:
                        menu_data[current_category] = []
                elif current_category is not None:
                    # Parse menu item line
                    items = self.parse_menu_item(line)
                    menu_data[current_category].extend(items)
        
        return menu_data
    
    def parse_menu_item(self, line):
        """Parse a menu item line and return a list of (name, price) tuples"""
        items = []
        
        # Pattern for items with multiple sizes: "NAME (S - X, L - Y)"
        multi_size_pattern = r'^(.+?)\s*\(([^)]+)\)\s*$'
        multi_match = re.match(multi_size_pattern, line)
        
        if multi_match:
            base_name = multi_match.group(1).strip()
            sizes_part = multi_match.group(2)
            
            # Parse each size option
            size_pattern = r'(\w+)\s*-\s*(\d+(?:\.\d+)?)'
            size_matches = re.findall(size_pattern, sizes_part)
            
            for size, price in size_matches:
                full_name = f"{base_name} {size}"
                items.append((full_name, Decimal(price)))
        else:
            # Pattern for single items: "NAME - X"
            single_pattern = r'^(.+?)\s*-\s*(\d+(?:\.\d+)?)\s*$'
            single_match = re.match(single_pattern, line)
            
            if single_match:
                name = single_match.group(1).strip()
                price = Decimal(single_match.group(2))
                items.append((name, price))
            else:
                self.stdout.write(self.style.WARNING(f"Could not parse line: {line}"))
        
        return items
    
    def _remove_outdated_menu_items(self, valid_items):
        """Remove menu items that are not present in the list of valid_items"""
        with transaction.atomic():
            # Build a list of (name, item_type) tuples that should be kept
            valid_combinations = set(valid_items)
            
            # Find all menu items that don't match any valid combination
            all_items = MenuItem.objects.all()
            items_to_delete = []
            
            for item in all_items:
                if (item.name, item.item_type) not in valid_combinations:
                    items_to_delete.append(item.id)
            
            if items_to_delete:
                # Delete the items that are not in the menu file
                deleted_count = MenuItem.objects.filter(id__in=items_to_delete).delete()[0]
                self.stdout.write(self.style.WARNING(
                    f"Deleted {deleted_count} menu items not present in the menu file"
                ))

    @retry_on_db_lock(max_retries=5, delay=1.0)
    def _process_menu_item(self, item_name, item_price, item_type, system_user, update_existing, clear_existing, valid_items):
        """Process a single menu item with retry logic for database locks"""
        with transaction.atomic():
            if (item_name, item_type) not in valid_items:
                return 'invalid'
            if update_existing or clear_existing:
                # Always use update_or_create when clear is used
                menu_item, created = MenuItem.objects.update_or_create(
                    name=item_name,
                    item_type=item_type,
                    defaults={
                        'price': item_price,
                        'is_available': True,
                        'created_by': system_user
                    }
                )
                if created:
                    return 'created'
                else:
                    # Update the existing item to be available again
                    if not menu_item.is_available:
                        menu_item.is_available = True
                        menu_item.price = item_price
                        menu_item.save()
                    return 'updated'
            else:
                # Check if item already exists
                if MenuItem.objects.filter(name=item_name, item_type=item_type).exists():
                    self.stdout.write(f"Skipped existing item: {item_name}")
                    return 'skipped'
                else:
                    MenuItem.objects.create(
                        name=item_name,
                        price=item_price,
                        item_type=item_type,
                        is_available=True,
                        created_by=system_user
                    )
                    return 'created'
