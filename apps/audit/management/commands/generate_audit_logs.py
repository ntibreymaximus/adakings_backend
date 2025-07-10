from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from apps.audit.models import AuditLog
from apps.orders.models import Order
from apps.menu.models import MenuItem

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate sample audit logs for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of audit logs to generate'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days back to generate logs for'
        )

    def handle(self, *args, **options):
        count = options['count']
        days = options['days']
        
        # Get users for logs
        users = list(User.objects.all())
        if not users:
            self.stdout.write(
                self.style.ERROR('No users found. Create some users first.')
            )
            return
        
        # Get some objects to create logs for
        orders = list(Order.objects.all())
        menu_items = list(MenuItem.objects.all())
        
        actions = [
            AuditLog.ACTION_CREATE,
            AuditLog.ACTION_UPDATE,
            AuditLog.ACTION_DELETE,
            AuditLog.ACTION_STATUS_CHANGE,
            AuditLog.ACTION_PAYMENT,
            AuditLog.ACTION_LOGIN,
            AuditLog.ACTION_LOGOUT,
        ]
        
        ip_addresses = [
            '192.168.1.100',
            '192.168.1.101',
            '10.0.0.50',
            '127.0.0.1',
            '172.16.0.10'
        ]
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        ]
        
        self.stdout.write(f'Generating {count} audit logs...')
        
        logs_created = 0
        base_time = timezone.now()
        
        for i in range(count):
            try:
                # Random timestamp within the specified days
                random_seconds = random.randint(0, days * 24 * 60 * 60)
                timestamp = base_time - timedelta(seconds=random_seconds)
                
                # Random user
                user = random.choice(users)
                
                # Random action
                action = random.choice(actions)
                
                # Random object (if available)
                content_object = None
                object_repr = None
                changes = {}
                
                if action in [AuditLog.ACTION_CREATE, AuditLog.ACTION_UPDATE, AuditLog.ACTION_DELETE]:
                    if orders and random.choice([True, False]):
                        content_object = random.choice(orders)
                        object_repr = str(content_object)
                        if action == AuditLog.ACTION_UPDATE:
                            changes = {
                                'status': {
                                    'old': random.choice(['Pending', 'Accepted']),
                                    'new': random.choice(['Accepted', 'Ready', 'Fulfilled'])
                                }
                            }
                    elif menu_items:
                        content_object = random.choice(menu_items)
                        object_repr = str(content_object)
                        if action == AuditLog.ACTION_UPDATE:
                            changes = {
                                'price': {
                                    'old': '10.00',
                                    'new': f'{random.uniform(5.0, 25.0):.2f}'
                                }
                            }
                
                elif action == AuditLog.ACTION_STATUS_CHANGE and orders:
                    content_object = random.choice(orders)
                    object_repr = str(content_object)
                    changes = {
                        'status': {
                            'old': random.choice(['Pending', 'Accepted']),
                            'new': random.choice(['Accepted', 'Ready', 'Fulfilled'])
                        }
                    }
                
                elif action == AuditLog.ACTION_PAYMENT and orders:
                    content_object = random.choice(orders)
                    object_repr = f'Payment for {content_object}'
                    changes = {
                        'amount': f'{random.uniform(10.0, 100.0):.2f}',
                        'payment_method': random.choice(['Cash', 'Mobile Money', 'Card']),
                        'processed': True
                    }
                
                # Create audit log
                log = AuditLog.objects.create(
                    user=user,
                    action=action,
                    timestamp=timestamp,
                    content_object=content_object,
                    object_repr=object_repr or f'{action} action',
                    changes=changes,
                    ip_address=random.choice(ip_addresses),
                    user_agent=random.choice(user_agents)
                )
                
                logs_created += 1
                
                if (i + 1) % 20 == 0:
                    self.stdout.write(f'Created {i + 1}/{count} logs...', ending='\\r')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error creating log {i + 1}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\\nSuccessfully created {logs_created} audit logs')
        )
