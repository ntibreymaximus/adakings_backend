from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserResource(resources.ModelResource):
    """Resource class for importing/exporting Custom Users"""
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'staff_id', 
                 'role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
        export_order = ('id', 'username', 'email', 'first_name', 'last_name', 'staff_id', 
                       'role', 'is_active', 'date_joined')
        import_id_fields = ('username',)
        skip_unchanged = True
        report_skipped = True
        exclude = ('password',)  # Don't export passwords

class CustomUserAdmin(UserAdmin, ImportExportModelAdmin):
    resource_class = CustomUserResource
    """
    Custom admin class for CustomUser model with role-based fields
    and enhanced user management capabilities.
    """
    # Forms to use for add and change
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    # Fields shown in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'staff_id', 
                    'role', 'is_active', 'date_joined')
    
    # Filters in the right sidebar
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    
    # Search functionality
    search_fields = ('username', 'email', 'first_name', 'last_name', 'staff_id')
    
    # Order users by
    ordering = ('-date_joined',)
    
    # Fields that are read-only in the admin change form
    readonly_fields = ('last_login', 'date_joined', 'staff_id')
    
    # Fields organization for the detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Role & Identification'), {'fields': ('role',)}), # staff_id removed, will be shown via readonly_fields
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields shown when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'), # staff_id removed
        }),
        (_('Personal info'), {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name'),
        }),
        (_('Permissions'), {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """
        Dynamically adjust fieldsets based on the user's role and permissions.
        Add role-specific fields for delivery staff.
        Restrict superuser field access to superusers only.
        """
        fieldsets = super().get_fieldsets(request, obj)
        
        # Convert to list for manipulation
        fieldsets = list(fieldsets)
        
        # For existing users with delivery role, add delivery-specific fields
        if obj and obj.role == CustomUser.DELIVERY:
            # Add delivery fields section
            fieldsets.insert(3, (_('Delivery Information'), {'fields': ('delivery_zone', 'vehicle_type')}))
        
        # Only superusers can modify superuser and staff status
        if not request.user.is_superuser:
            for i, (name, opts) in enumerate(fieldsets):
                if name == 'Permissions':
                    fields = list(opts.get('fields', []))
                    # Remove superuser field from non-superusers
                    if 'is_superuser' in fields:
                        fields.remove('is_superuser')
                    # Remove staff field from non-superusers (auto-managed by role)
                    if 'is_staff' in fields:
                        fields.remove('is_staff')
                    # Also restrict user_permissions and groups for admin users
                    # Only superusers can assign specific permissions
                    if 'user_permissions' in fields:
                        fields.remove('user_permissions')
                    if 'groups' in fields:
                        fields.remove('groups')
                    fieldsets[i] = (name, {**opts, 'fields': tuple(fields)})
            
        return fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Dynamically adjust the form to include delivery-specific fields 
        and restrict superuser field access.
        """
        form = super().get_form(request, obj, **kwargs)
        
        # For delivery staff, ensure fields are in the form
        if obj and obj.role == CustomUser.DELIVERY:
            if 'delivery_zone' not in form.base_fields:
                form.base_fields['delivery_zone'] = CustomUserChangeForm.base_fields['delivery_zone']
            if 'vehicle_type' not in form.base_fields:
                form.base_fields['vehicle_type'] = CustomUserChangeForm.base_fields['vehicle_type']
        
        # Only superusers can modify superuser and staff status
        if not request.user.is_superuser:
            if 'is_superuser' in form.base_fields:
                del form.base_fields['is_superuser']
            if 'is_staff' in form.base_fields:
                del form.base_fields['is_staff']
            
        return form
    
    def changelist_view(self, request, extra_context=None):
        """Add informational message about staff status management."""
        extra_context = extra_context or {}
        
        from django.contrib import messages
        messages.info(
            request, 
            "Staff status (Django admin access) is automatically managed based on user role. "
            "Only superadmins can access Django admin. All other roles (including admin) use the API interface."
        )
        
        return super().changelist_view(request, extra_context)

# Register the model with the custom admin
admin.site.register(CustomUser, CustomUserAdmin)
