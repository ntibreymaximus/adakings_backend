from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.menu.models import MenuItem
from apps.menu.serializers import MenuItemSerializer

User = get_user_model()


class SimplePrefixingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
    def test_serializer_prefix_logic(self):
        """Test the serializer's validate_name method directly"""
        serializer = MenuItemSerializer()
        
        # Test BOLT prefix
        serializer.initial_data = {'item_type': 'bolt'}
        self.assertEqual(
            serializer.validate_name('Burger'),
            'BOLT-Burger'
        )
        
        # Test WIX prefix
        serializer.initial_data = {'item_type': 'wix'}
        self.assertEqual(
            serializer.validate_name('Pizza'),
            'WIX-Pizza'
        )
        
        # Test regular item (no prefix)
        serializer.initial_data = {'item_type': 'regular'}
        self.assertEqual(
            serializer.validate_name('Sandwich'),
            'Sandwich'
        )
        
        # Test extra item (no prefix)
        serializer.initial_data = {'item_type': 'extra'}
        self.assertEqual(
            serializer.validate_name('Cheese'),
            'Cheese'
        )
        
    def test_serializer_no_double_prefix(self):
        """Test that existing prefixes are not duplicated"""
        serializer = MenuItemSerializer()
        
        # Test BOLT with existing prefix
        serializer.initial_data = {'item_type': 'bolt'}
        self.assertEqual(
            serializer.validate_name('BOLT-Already Prefixed'),
            'BOLT-Already Prefixed'
        )
        
        # Test WIX with existing prefix
        serializer.initial_data = {'item_type': 'wix'}
        self.assertEqual(
            serializer.validate_name('WIX-Already Prefixed'),
            'WIX-Already Prefixed'
        )
        
    def test_prefix_removal_when_changing_type(self):
        """Test that prefixes are handled correctly when changing item types"""
        serializer = MenuItemSerializer()
        
        # Changing from BOLT to regular should remove prefix
        serializer.initial_data = {'item_type': 'regular'}
        self.assertEqual(
            serializer.validate_name('BOLT-Item'),
            'Item'
        )
        
        # Changing from WIX to regular should remove prefix
        serializer.initial_data = {'item_type': 'regular'}
        self.assertEqual(
            serializer.validate_name('WIX-Item'),
            'Item'
        )
        
        # Changing from regular to BOLT should add prefix
        serializer.initial_data = {'item_type': 'bolt'}
        self.assertEqual(
            serializer.validate_name('Item'),
            'BOLT-Item'
        )
        
        # Changing from BOLT to WIX should switch prefix
        serializer.initial_data = {'item_type': 'wix'}
        self.assertEqual(
            serializer.validate_name('BOLT-Item'),
            'WIX-Item'
        )
