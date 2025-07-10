from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import AuditLog, UserActivitySummary


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 
        'user_display', 
        'action', 
        'object_display',
        'app_label',
        'model_name',
        'ip_address'
    ]
    
    list_filter = [
        'action',
        'timestamp',
        'app_label',
        'model_name',
        'user'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'object_repr',
        'ip_address'
    ]
    
    readonly_fields = [
        'user',
        'action',
        'timestamp',
        'content_type',
        'object_id',
        'object_link',
        'object_repr',
        'changes_display',
        'ip_address',
        'user_agent',
        'app_label',
        'model_name'
    ]
    
    ordering = ['-timestamp']
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username} ({obj.user.get_full_name() or 'No name'})"
        return "System"
    user_display.short_description = 'User'
    
    def object_display(self, obj):
        return obj.object_repr or "N/A"
    object_display.short_description = 'Object'
    
    def object_link(self, obj):
        if obj.content_type and obj.object_id:
            try:
                url = reverse(
                    f'admin:{obj.app_label}_{obj.model_name}_change',
                    args=[obj.object_id]
                )
                return format_html('<a href="{}">View {}</a>', url, obj.object_repr)
            except:
                return f"{obj.object_repr} (link not available)"
        return "N/A"
    object_link.short_description = 'Object Link'
    
    def changes_display(self, obj):
        if obj.changes:
            formatted = json.dumps(obj.changes, indent=2)
            return format_html('<pre>{}</pre>', formatted)
        return "No changes recorded"
    changes_display.short_description = 'Changes'
    
    def has_add_permission(self, request):
        # Audit logs should not be manually created
        return False
    
    def has_change_permission(self, request, obj=None):
        # Audit logs should not be edited
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser


@admin.register(UserActivitySummary)
class UserActivitySummaryAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'date',
        'total_actions',
        'creates',
        'updates',
        'deletes',
        'payments',
        'last_activity'
    ]
    
    list_filter = [
        'date',
        'user'
    ]
    
    search_fields = [
        'user__username',
        'user__email'
    ]
    
    ordering = ['-date', 'user']
    
    readonly_fields = [
        'user',
        'date',
        'total_actions',
        'creates',
        'updates',
        'deletes',
        'payments',
        'last_activity'
    ]
    
    def has_add_permission(self, request):
        # Summaries are auto-generated
        return False
    
    def has_change_permission(self, request, obj=None):
        # Summaries should not be edited
        return False
