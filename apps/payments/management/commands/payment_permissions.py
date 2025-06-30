from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = """
    Displays information about payment transaction permissions and superuser requirements.
    
    PAYMENT TRANSACTION DELETION POLICY:
    - Only SUPERADMINS can delete payment transactions from the Django admin
    - Regular admins and staff CANNOT delete payment transactions
    - This ensures financial audit compliance and data integrity
    
    DJANGO ADMIN ACCESS POLICY:
    - Only SUPERADMINS have Django admin access (is_staff=True)
    - ALL other roles (admin, frontdesk, kitchen, delivery) use API interface only
    - Staff status is automatically managed based on user role
    
    SUPERUSER CREATION:
    - Superadmins can ONLY be created using: python manage.py createsuperuser
    - Regular admins CANNOT grant superuser status to other users
    - Superuser status CANNOT be granted through the Django admin by non-superusers
    """

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== PAYMENT TRANSACTION PERMISSIONS ==='))
        self.stdout.write('')
        
        # Display policy information
        self.stdout.write(self.style.WARNING('DELETION POLICY:'))
        self.stdout.write('• Only SUPERUSERS can delete payment transactions')
        self.stdout.write('• Regular admins and staff CANNOT delete transactions')
        self.stdout.write('• This ensures financial audit compliance')
        self.stdout.write('')
        
        self.stdout.write(self.style.WARNING('SUPERUSER CREATION:'))
        self.stdout.write('• Superusers can ONLY be created via: python manage.py createsuperuser')
        self.stdout.write('• Regular admins CANNOT grant superuser status')
        self.stdout.write('• Superuser field is hidden from non-superusers in admin')
        self.stdout.write('')
        
        # List current superusers
        superusers = User.objects.filter(is_superuser=True, is_active=True)
        
        if superusers.exists():
            self.stdout.write(self.style.SUCCESS('CURRENT ACTIVE SUPERUSERS:'))
            for user in superusers:
                self.stdout.write(f'• {user.username} ({user.email}) - Created: {user.date_joined.strftime("%Y-%m-%d")}')
        else:
            self.stdout.write(self.style.ERROR('NO ACTIVE SUPERUSERS FOUND!'))
            self.stdout.write('Create one with: python manage.py createsuperuser')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== END PAYMENT PERMISSIONS INFO ==='))

