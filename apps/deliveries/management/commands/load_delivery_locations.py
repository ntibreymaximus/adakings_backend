import os
import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.deliveries.models import DeliveryLocation


class Command(BaseCommand):
    help = 'Load delivery locations from delivery locations.txt file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='delivery locations.txt',
            help='Path to the delivery locations file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing locations before loading new ones'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing locations if they exist'
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
        
        # Clear existing locations if requested
        if clear_existing:
            count = DeliveryLocation.objects.count()
            DeliveryLocation.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing locations"))
        
        # Parse the file
        locations_data = self.parse_delivery_file(file_path)
        
        # Load locations into database
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for price, locations in locations_data.items():
            for location_name in locations:
                location_name = location_name.strip()
                if not location_name:
                    continue
                
                if update_existing:
                    location, created = DeliveryLocation.objects.update_or_create(
                        name=location_name,
                        defaults={
                            'fee': price,
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                else:
                    # Check if location already exists
                    if DeliveryLocation.objects.filter(name=location_name).exists():
                        skipped_count += 1
                        self.stdout.write(f"Skipped existing location: {location_name}")
                    else:
                        DeliveryLocation.objects.create(
                            name=location_name,
                            fee=price,
                            is_active=True
                        )
                        created_count += 1
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\nSummary:\n"
            f"  Created: {created_count} locations\n"
            f"  Updated: {updated_count} locations\n"
            f"  Skipped: {skipped_count} locations\n"
            f"  Total in database: {DeliveryLocation.objects.count()} locations"
        ))
        
        # Show all locations grouped by price
        self.stdout.write("\nCurrent delivery locations by price:")
        for location in DeliveryLocation.objects.all().order_by('fee', 'name'):
            self.stdout.write(f"  ₵{location.fee:.2f} - {location.name}")
    
    def parse_delivery_file(self, file_path):
        """Parse the delivery locations file and return a dictionary of {price: [locations]}"""
        locations_data = {}
        current_price = None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if not line:
                    continue
                
                # Check if this is a price line
                price_match = re.match(r'\{DELIVERY PRICE\}\s*-\s*(\d+(?:\.\d+)?)', line)
                if price_match:
                    current_price = Decimal(price_match.group(1))
                    if current_price not in locations_data:
                        locations_data[current_price] = []
                elif current_price is not None:
                    # This is a location line
                    locations_data[current_price].append(line)
        
        return locations_data
