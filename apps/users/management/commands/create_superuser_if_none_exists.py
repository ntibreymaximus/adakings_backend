from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates a superuser with specific credentials if none exist, based on the environment.'

    def handle(self, *args, **options):
        User = get_user_model()

        # Check the environment
        is_debug = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'on', 'yes')
        env_name = 'development' if is_debug else 'production'

        # Credentials based on environment
        if env_name == 'development':
            username, password = 'admin', 'admin2025'
        else:
            username, password = 'superadmin', 'SuperAdmin2025'

        # Ensure the superuser exists
        if not User.objects.filter(username=username, is_superuser=True).exists():
            User.objects.create_superuser(username=username, email=f'{username}@adakings.com', password=password)
            self.stdout.write(self.style.SUCCESS(f'Superuser {username} created successfully in {env_name} environment.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superuser {username} already exists in {env_name} environment.'))

