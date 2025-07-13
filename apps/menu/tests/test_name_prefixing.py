from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.menu.models import MenuItem
from apps.menu.serializers import MenuItemSerializer

User = get_user_model()


class MenuItemNamePrefixingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def test_bolt_item_name_prefixing(self):
        """Test that Bolt items automatically get BOLT- prefix"""
        # Create a Bolt item without prefix
        data = {
            'name': 'Burger',
            'item_type': 'bolt',
            'price': '10.00',
            'is_available': True
        }
        
        response = self.client.post('/api/menu/items/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the name was prefixed
        item = MenuItem.objects.get(id=response.data['id'])
        self.assertEqual(item.name, 'BOLT-Burger')
        
    def test_wix_item_name_prefixing(self):
        """Test that WIX items automatically get WIX- prefix"""
        # Create a WIX item without prefix
        data = {
            'name': 'Pizza',
            'item_type': 'wix',
            'price': '15.00',
            'is_available': True
        }
        
        response = self.client.post('/api/menu/items/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the name was prefixed
        item = MenuItem.objects.get(id=response.data['id'])
        self.assertEqual(item.name, 'WIX-Pizza')
        
    def test_regular_item_no_prefix(self):
        """Test that regular items don't get a prefix"""
        data = {
            'name': 'Regular Sandwich',
            'item_type': 'regular',
            'price': '8.00',
            'is_available': True
        }
        
        response = self.client.post('/api/menu/items/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the name was not prefixed
        item = MenuItem.objects.get(id=response.data['id'])
        self.assertEqual(item.name, 'Regular Sandwich')
        
    def test_extra_item_no_prefix(self):
        """Test that extra items don't get a prefix"""
        data = {
            'name': 'Extra Cheese',
            'item_type': 'extra',
            'price': '2.00',
            'is_available': True
        }
        
        response = self.client.post('/api/menu/items/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the name was not prefixed
        item = MenuItem.objects.get(id=response.data['id'])
        self.assertEqual(item.name, 'Extra Cheese')
        
    def test_bolt_item_with_existing_prefix(self):
        """Test that Bolt items with existing prefix don't get double-prefixed"""
        data = {
            'name': 'BOLT-Already Prefixed',
            'item_type': 'bolt',
            'price': '12.00',
            'is_available': True
        }
        
        response = self.client.post('/api/menu/items/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the name wasn't double-prefixed
        item = MenuItem.objects.get(id=response.data['id'])
        self.assertEqual(item.name, 'BOLT-Already Prefixed')
        
    def test_update_item_type_updates_prefix(self):
        """Test that changing item type updates the prefix appropriately"""
        # Create a regular item
        item = MenuItem.objects.create(
            name='Test Item',
            item_type='regular',
            price='10.00',
            is_available=True,
            created_by=self.user
        )
        
        # Update it to be a Bolt item
        data = {
            'item_type': 'bolt',
            'name': 'Test Item',
            'price': '10.00',
            'is_available': True
        }
        
        response = self.client.patch(f'/api/menu/items/{item.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the name was prefixed
        item.refresh_from_db()
        self.assertEqual(item.name, 'BOLT-Test Item')
        
    def test_serializer_validate_name_method(self):
        """Test the serializer's validate_name method directly"""
        serializer = MenuItemSerializer()
        
        # Test Bolt prefix
        serializer.initial_data = {'item_type': 'bolt'}
        validated_name = serializer.validate_name('Test Item')
        self.assertEqual(validated_name, 'BOLT-Test Item')
        
        # Test WIX prefix
        serializer.initial_data = {'item_type': 'wix'}
        validated_name = serializer.validate_name('Test Item')
        self.assertEqual(validated_name, 'WIX-Test Item')
        
        # Test regular (no prefix)
        serializer.initial_data = {'item_type': 'regular'}
        validated_name = serializer.validate_name('Test Item')
        self.assertEqual(validated_name, 'Test Item')
