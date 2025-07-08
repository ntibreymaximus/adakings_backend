"""
Django management command for environment checking.
Usage: python manage.py checkenv
"""

from django.core.management.base import BaseCommand
from django.core.management import CommandError
import sys
import os

class Command(BaseCommand):
    help = 'Check Django environment configuration and validate settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fail-on-error',
            action='store_true',
            help='Exit with error code if validation fails (default: True)',
        )
        parser.add_argument(
            '--no-fail-on-error',
            action='store_true',
            help='Continue even if validation fails',
        )

    def handle(self, *args, **options):
        try:
            # Import the check_environment function
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            sys.path.insert(0, project_root)
            from check_environment import check_environment
            
            # Run the environment check
            validation_passed, env_type = check_environment()
            
            if validation_passed:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Environment configuration is correct for {env_type}!')
                )
                return
            else:
                error_msg = f'❌ Environment configuration issues detected in {env_type}!'
                
                if options['no_fail_on_error']:
                    self.stdout.write(self.style.WARNING(error_msg))
                    self.stdout.write(self.style.WARNING('⚠️  Continuing despite validation errors...'))
                else:
                    self.stdout.write(self.style.ERROR(error_msg))
                    raise CommandError('Environment validation failed!')
                    
        except ImportError as e:
            raise CommandError(f'Could not import check_environment: {e}')
        except Exception as e:
            raise CommandError(f'Error during environment check: {e}')
