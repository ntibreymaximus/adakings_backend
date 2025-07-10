from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AuditLog, UserActivitySummary

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for audit logs"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class AuditLogSerializer(serializers.ModelSerializer):
    """Comprehensive audit log serializer"""
    user = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    object_type = serializers.SerializerMethodField()
    formatted_changes = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user',
            'action',
            'action_display',
            'timestamp',
            'time_ago',
            'object_type',
            'object_id',
            'object_repr',
            'changes',
            'formatted_changes',
            'ip_address',
            'user_agent',
            'app_label',
            'model_name'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_time_ago(self, obj):
        """Get human-readable time since the action"""
        from django.utils.timesince import timesince
        from django.utils import timezone
        
        now = timezone.now()
        time_diff = now - obj.timestamp
        
        # If less than 30 seconds ago, show "Just now"
        if time_diff.total_seconds() < 30:
            return "Just now"
        
        return timesince(obj.timestamp, now) + " ago"
    
    def get_object_type(self, obj):
        """Get readable object type"""
        if obj.app_label and obj.model_name:
            return f"{obj.app_label.title()} {obj.model_name.title()}"
        return "Unknown"
    
    def get_formatted_changes(self, obj):
        """Format changes for frontend display"""
        if not obj.changes:
            return []
        
        formatted = []
        for field, change in obj.changes.items():
            if isinstance(change, dict) and 'old' in change and 'new' in change:
                formatted.append({
                    'field': field.replace('_', ' ').title(),
                    'old_value': change['old'],
                    'new_value': change['new'],
                    'field_key': field
                })
            else:
                # Handle other change formats
                formatted.append({
                    'field': field.replace('_', ' ').title(),
                    'value': str(change),
                    'field_key': field
                })
        
        return formatted


class UserActivitySummarySerializer(serializers.ModelSerializer):
    """Serializer for user activity summaries"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserActivitySummary
        fields = [
            'id',
            'user',
            'date',
            'total_actions',
            'creates',
            'updates',
            'deletes',
            'payments',
            'last_activity'
        ]
