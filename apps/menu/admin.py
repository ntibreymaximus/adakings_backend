from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import MenuItem

class MenuItemResource(resources.ModelResource):
    """Resource class for importing/exporting Menu Items"""
    class Meta:
        model = MenuItem
        fields = ('id', 'name', 'item_type', 'price', 'is_available', 'created_by', 'created_at', 'updated_at')
        export_order = ('id', 'name', 'item_type', 'price', 'is_available', 'created_at')
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True

@admin.register(MenuItem)
class MenuItemAdmin(ImportExportModelAdmin):
    resource_class = MenuItemResource
    list_display = ['name', 'item_type', 'price', 'is_available', 'created_by', 'created_at']
    list_filter = ['item_type', 'is_available', 'created_at']
    search_fields = ['name']
    ordering = ['item_type', 'name']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'item_type', 'price', 'is_available')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def has_view_permission(self, request, obj=None):
        """All staff can view menu items"""
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        """Only superusers and admin role users can modify menu items"""
        return request.user.is_superuser or (request.user.is_staff and request.user.role == 'admin')

    def has_add_permission(self, request):
        """Only superusers and admin role users can add menu items"""
        return request.user.is_superuser or (request.user.is_staff and request.user.role == 'admin')

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete menu items"""
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

