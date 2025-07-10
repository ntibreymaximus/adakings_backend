from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class AuditLog(models.Model):
    """
    Model to track user actions across the system.
    Records who did what, when, and on which object.
    """
    
    # Action types
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_STATUS_CHANGE = 'status_change'
    ACTION_PAYMENT = 'payment'
    ACTION_REFUND = 'refund'
    ACTION_TOGGLE = 'toggle'
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_STATUS_CHANGE, 'Status Change'),
        (ACTION_PAYMENT, 'Payment'),
        (ACTION_REFUND, 'Refund'),
        (ACTION_TOGGLE, 'Toggle'),
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
    ]
    
    # User who performed the action
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional metadata
    object_repr = models.CharField(max_length=200, blank=True)  # String representation of the object
    changes = models.JSONField(default=dict, blank=True)  # JSON field for storing what changed
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Optional fields for specific contexts
    app_label = models.CharField(max_length=100, blank=True, db_index=True)
    model_name = models.CharField(max_length=100, blank=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['app_label', 'model_name', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.object_repr} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        # Auto-populate app_label and model_name if content_type is set
        if self.content_type:
            self.app_label = self.content_type.app_label
            self.model_name = self.content_type.model
        
        # Try to get string representation of the object
        if self.content_object and not self.object_repr:
            try:
                self.object_repr = str(self.content_object)
            except:
                self.object_repr = f"{self.model_name} #{self.object_id}"
        
        super().save(*args, **kwargs)
    
    @classmethod
    def log_action(cls, user, action, obj=None, changes=None, request=None):
        """
        Convenience method to create an audit log entry.
        
        Args:
            user: User instance who performed the action
            action: Action type (from ACTION_CHOICES)
            obj: The object being acted upon (optional)
            changes: Dict of changes made (optional)
            request: HttpRequest object to extract IP and user agent (optional)
        
        Returns:
            AuditLog instance
        """
        log_entry = cls(user=user, action=action)
        
        if obj:
            log_entry.content_type = ContentType.objects.get_for_model(obj)
            log_entry.object_id = obj.pk
            log_entry.content_object = obj
        
        if changes:
            log_entry.changes = changes
        
        if request:
            # Extract IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                log_entry.ip_address = x_forwarded_for.split(',')[0]
            else:
                log_entry.ip_address = request.META.get('REMOTE_ADDR')
            
            # Extract user agent
            log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        log_entry.save()
        return log_entry


class UserActivitySummary(models.Model):
    """
    Aggregated view of user activities for reporting purposes.
    This can be populated via periodic tasks or signals.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_summaries')
    date = models.DateField(db_index=True)
    
    # Activity counts
    total_actions = models.PositiveIntegerField(default=0)
    creates = models.PositiveIntegerField(default=0)
    updates = models.PositiveIntegerField(default=0)
    deletes = models.PositiveIntegerField(default=0)
    payments = models.PositiveIntegerField(default=0)
    
    # Last activity
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name = 'User Activity Summary'
        verbose_name_plural = 'User Activity Summaries'
    
    def __str__(self):
        return f"{self.user} - {self.date} - {self.total_actions} actions"
