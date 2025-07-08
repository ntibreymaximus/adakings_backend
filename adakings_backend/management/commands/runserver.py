"""
Custom runserver command that runs environment check before starting the server.
Overrides Django's default runserver command.
"""

from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.management import CommandError
import sys
import os

class Command(RunserverCommand):
    help = 'Start development server with environment validation'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--skip-env-check',
            action='store_true',
            help='Skip environment validation check',
        )

    def handle(self, *args, **options):
        # Run environment check unless explicitly skipped
        if not options.get('skip_env_check', False):
            self.stdout.write('🔍 Running environment configuration check...')
            self.stdout.write('-' * 50)
            
            try:
                # Import the check_environment function
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                sys.path.insert(0, project_root)
                from check_environment import check_environment
                
                # Run the environment check
                validation_passed, env_type = check_environment()
                
                if not validation_passed:
                    self.stdout.write(
                        self.style.ERROR('❌ Environment validation failed! Please fix the issues above.')
                    )
                    self.stdout.write(
                        self.style.ERROR('Use --skip-env-check to bypass this check (not recommended).')
                    )
                    raise CommandError('Environment validation failed!')
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Environment check passed for {env_type}!')
                )
                self.stdout.write('🚀 Starting Django development server...')
                self.stdout.write('=' * 50)
                
            except ImportError as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Could not run environment check: {e}')
                )
                self.stdout.write(
                    self.style.WARNING('⚠️  Proceeding with server start anyway...')
                )
                self.stdout.write('=' * 50)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Environment check failed: {e}')
                )
                self.stdout.write(
                    self.style.WARNING('⚠️  Proceeding with server start anyway...')
                )
                self.stdout.write('=' * 50)
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Environment check skipped!')
            )
            self.stdout.write('🚀 Starting Django development server...')
            self.stdout.write('=' * 50)

        # Call the parent runserver command
        super().handle(*args, **options)
