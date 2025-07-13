from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import MenuItem

class MenuItemSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    is_extra = serializers.SerializerMethodField() # Changed from ReadOnlyField
    is_bolt = serializers.SerializerMethodField()
    is_wix = serializers.SerializerMethodField()

    @extend_schema_field(serializers.BooleanField())
    def get_is_extra(self, obj: MenuItem) -> bool:
        return obj.is_extra
    
    @extend_schema_field(serializers.BooleanField())
    def get_is_bolt(self, obj: MenuItem) -> bool:
        return obj.is_bolt
    
    @extend_schema_field(serializers.BooleanField())
    def get_is_wix(self, obj: MenuItem) -> bool:
        return obj.is_wix

    def validate_name(self, value):
        """Ensure name has appropriate prefix based on item_type"""
        item_type = self.initial_data.get('item_type', 'regular')
        
        # For updates, check if we're changing the item_type
        if self.instance:
            item_type = self.initial_data.get('item_type', self.instance.item_type)
        
        # Clean the name by removing any existing prefixes
        clean_name = value
        if clean_name.startswith('BOLT-'):
            clean_name = clean_name[5:]
        elif clean_name.startswith('WIX-'):
            clean_name = clean_name[4:]
        
        # Add appropriate prefix based on item_type
        if item_type == 'bolt':
            return f'BOLT-{clean_name}'
        elif item_type == 'wix':
            return f'WIX-{clean_name}'
        else:
            # For regular and extra items, use the clean name without prefix
            return clean_name

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'item_type', 'price', 'is_available', 'created_by', 'created_at', 'updated_at', 'is_extra', 'is_bolt', 'is_wix']
        read_only_fields = ['created_at', 'updated_at']

class MenuItemToggleAvailabilitySerializer(serializers.Serializer):
    # No input needed for this action, but serializer can be used for validation or future extensions
    pass

