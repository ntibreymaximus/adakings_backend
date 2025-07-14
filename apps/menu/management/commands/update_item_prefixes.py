from django.core.management.base import BaseCommand
from django.db import transaction
from apps.menu.models import MenuItem


class Command(BaseCommand):
    help = 'Updates menu item names to include proper prefixes for Bolt items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('Starting menu item prefix update...')
        
        # Process Bolt items
        bolt_items = MenuItem.objects.filter(item_type='bolt')
        bolt_updated = 0
        
        for item in bolt_items:
            if not item.name.startswith('BOLT-'):
                old_name = item.name
                new_name = f'BOLT-{old_name}'
                
                if dry_run:
                    self.stdout.write(f'Would update Bolt item: "{old_name}" -> "{new_name}"')
                else:
                    item.name = new_name
                    item.save()
                    self.stdout.write(self.style.SUCCESS(f'Updated Bolt item: "{old_name}" -> "{new_name}"'))
                
                bolt_updated += 1
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDry run complete. Would update {bolt_updated} Bolt items.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nUpdate complete. Updated {bolt_updated} Bolt items.'
                )
            )
        
        # Show current status
        total_bolt = MenuItem.objects.filter(item_type='bolt').count()
        prefixed_bolt = MenuItem.objects.filter(item_type='bolt', name__startswith='BOLT-').count()
        
        self.stdout.write(
            f'\nCurrent status:\n'
            f'  Bolt items: {prefixed_bolt}/{total_bolt} have proper prefix'
        )
