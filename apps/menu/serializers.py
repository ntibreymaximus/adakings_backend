from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import MenuItem

class MenuItemSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    is_extra = serializers.SerializerMethodField() # Changed from ReadOnlyField

    @extend_schema_field(serializers.BooleanField())
    def get_is_extra(self, obj: MenuItem) -> bool:
        return obj.is_extra

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'item_type', 'price', 'is_available', 'created_by', 'created_at', 'updated_at', 'is_extra']
        read_only_fields = ['created_at', 'updated_at']

class MenuItemToggleAvailabilitySerializer(serializers.Serializer):
    # No input needed for this action, but serializer can be used for validation or future extensions
    pass

