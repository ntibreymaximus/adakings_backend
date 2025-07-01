from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Run the server in a specific environment'

    def add_arguments(self, parser):
        parser.add_argument('environment', type=str, help='The environment to run the server in (dev, prod, or local)')

    def handle(self, *args, **options):
        environment = options['environment'].lower()

        # Set environment variable
        if environment == 'prod':
            os.environ['DJANGO_ENVIRONMENT'] = 'production'
            settings_module = 'adakings_backend.settings.production'
        elif environment == 'dev':
            os.environ['DJANGO_ENVIRONMENT'] = 'dev'
            settings_module = 'adakings_backend.settings.dev'
        elif environment == 'local':
            os.environ['DJANGO_ENVIRONMENT'] = 'development'
            settings_module = 'adakings_backend.settings.development'
        else:
            self.stdout.write(self.style.ERROR('Invalid environment specified. Use dev, prod, or local.'))
            return

        # Set the settings module
        os.environ['DJANGO_SETTINGS_MODULE'] = settings_module

        # Launch development server
        self.stdout.write(self.style.SUCCESS(f'Starting server in {environment} environment using {settings_module}'))
        os.system('python manage.py runserver')

