from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from .models import CustomUser

class UserAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Admin User
        self.admin_user = CustomUser.objects.create_user(
            username='admin', 
            password='adminpass', 
            email='admin@example.com',
            role=CustomUser.ADMIN,
            is_staff=True, 
            is_superuser=True
        )
        # Normal User
        self.normal_user = CustomUser.objects.create_user(
            username='testuser', 
            password='testpass123', 
            email='testuser@example.com',
            role=CustomUser.FRONTDESK
        )
        # Staff User (for management tests)
        self.staff_user_data = {
            'username': 'staffmember',
            'password': 'staffpass',
            'email': 'staff@example.com',
            'first_name': 'Staff',
            'last_name': 'Member',
            'role': CustomUser.KITCHEN
        }

    # Registration Tests
    def test_user_registration(self):
        url = reverse('users_api:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': CustomUser.DELIVERY
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())

    def test_user_registration_password_mismatch(self):
        url = reverse('users_api:register')
        data = {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'newpass123',
            'password2': 'mismatch',
            'first_name': 'New',
            'last_name': 'User',
            'role': CustomUser.FRONTDESK
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    # Login/Logout Tests
    def test_user_login(self):
        url = reverse('users_api:login')
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)

    def test_user_login_invalid_credentials(self):
        url = reverse('users_api:login')
        data = {'username': 'testuser', 'password': 'wrongpassword'}
        response = self.client.post(url, data, format='json')
        # This will depend on how your UserLoginSerializer handles auth failure
        # If it raises AuthenticationFailed, it will be 401. If validation error, 400.
        # Assuming a generic error or that the view catches and returns 400 for simplicity
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])

    def test_user_logout(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('users_api:logout')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Profile Tests
    def test_get_profile_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        # Assuming your UserViewSet has a 'me' action or similar for current user profile
        url = reverse('users_api:user-me') # DefaultRouter creates 'basename-me' for @action(detail=False) 
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_get_profile_unauthenticated(self):
        url = reverse('users_api:user-me')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('users_api:profile') 
        data = {'first_name': 'Updated', 'last_name': 'Name', 'email': 'updated@example.com'}
        response = self.client.put(url, data, format='json') # Or PATCH if partial updates are allowed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.first_name, 'Updated')

    # Password Reset (Simplified - not testing email sending)
    def test_password_reset_request(self):
        url = reverse('users_api:password_reset')
        data = {'email': self.normal_user.email}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    # Staff Management Tests (Admin Only)
    def test_list_staff_as_admin(self):
        self.client.login(username='admin', password='adminpass')
        url = reverse('users_api:staff-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if normal_user (who is staff based on model) is in the list
        # self.assertGreater(len(response.data), 0)

    def test_list_staff_as_non_admin(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('users_api:staff-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_staff_as_admin(self):
        self.client.login(username='admin', password='adminpass')
        url = reverse('users_api:staff-list') # POST to list endpoint for ViewSet create
        response = self.client.post(url, self.staff_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(username='staffmember').exists())

    def test_create_staff_as_non_admin(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('users_api:staff-list')
        response = self.client.post(url, self.staff_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_staff_as_admin(self):
        self.client.login(username='admin', password='adminpass')
        # Create a staff user first to retrieve
        staff = CustomUser.objects.create_user(**self.staff_user_data)
        url = reverse('users_api:staff-detail', kwargs={'pk': staff.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.staff_user_data['username'])

    def test_update_staff_as_admin(self):
        self.client.login(username='admin', password='adminpass')
        staff = CustomUser.objects.create_user(**self.staff_user_data)
        url = reverse('users_api:staff-detail', kwargs={'pk': staff.pk})
        update_data = {'first_name': 'UpdatedStaff', 'role': CustomUser.ADMIN}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        staff.refresh_from_db()
        self.assertEqual(staff.first_name, 'UpdatedStaff')

    def test_delete_staff_as_admin(self):
        self.client.login(username='admin', password='adminpass')
        staff = CustomUser.objects.create_user(**self.staff_user_data)
        url = reverse('users_api:staff-detail', kwargs={'pk': staff.pk})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CustomUser.objects.filter(username=self.staff_user_data['username']).exists())

    # Add more tests, e.g. for password reset confirm, specific field validations etc.

