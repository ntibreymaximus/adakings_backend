from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates a superuser if none exist'

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS('Superuser already exists, skipping creation.'))
        else:
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'superadmin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@adakings.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'AdakingsSuperAdmin2025!')

            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser {username} created successfully.'))

