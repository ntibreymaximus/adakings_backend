from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode # Added urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str # Added force_str
from django.contrib.auth.tokens import default_token_generator
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import CustomUser
from .permissions import IsSuperadminOnly, IsAdminOrSuperuser
from .serializers import (
    CustomUserSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    ProfileUpdateSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    StaffManagementSerializer,
)

@extend_schema(
    summary="Manage Users (Admin)",
    description="Allows administrators to list, retrieve, create, update, and delete user accounts.",
    tags=['Users']
)
class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    serializer_class = CustomUserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return CustomUser.objects.all().order_by('id')

    def get_permissions(self):
        if self.action in ['create']:
            # Typically admin creates users, registration is separate. 
            # If create is open, it should probably use UserRegistrationSerializer or similar
            # For now, sticking to IsAdminUser for direct creation via this viewset.
            # If AllowAny was intended for self-registration through this viewset, consider UserRegistrationView.
            pass 
        return super().get_permissions()

    @extend_schema(
        summary="Get Current User Details",
        description="Retrieves the profile information for the currently authenticated user.",
        tags=['Users']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

@extend_schema(
    summary="Register New User",
    description="Allows new users to register an account. Returns user details upon successful registration.",
    tags=['Users']
)
class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

@extend_schema(
    summary="User Login",
    description="Authenticates a user and returns user details and a success message upon successful login.",
    tags=['Users']
)
class UserLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @extend_schema(exclude=True) # Exclude schema for GET on login view if it just serves the serializer fields
    def get(self, request, *args, **kwargs):
        # This GET method might be for rendering a login form in browsable API, or can be removed if not needed.
        # For schema purposes, typically only POST is documented for login.
        serializer = self.serializer_class()
        return Response(serializer.data) # Or an empty dict/message

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            return Response({
                'user': CustomUserSerializer(user).data,
                'access': str(access_token),
                'refresh': str(refresh),
                'message': 'Login successful'
            })
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_400_BAD_REQUEST
            )

@extend_schema(
    summary="User Logout",
    description="Logs out the currently authenticated user and invalidates their session.",
    request=None, # No request body
    responses={200: {'description': 'Logout successful'}},
    tags=['Users']
)
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    # serializer_class = None # Not needed if request is None

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})

@extend_schema(
    summary="Update User Profile",
    description="Allows the currently authenticated user to update their profile information (e.g., email, first name, last name).",
    tags=['Users']
)
class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

@extend_schema(
    summary="Request Password Reset",
    description="Initiates the password reset process for a user. An email with a reset link will be sent to the user's registered email address.",
    tags=['Users']
)
class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = get_object_or_404(CustomUser, email=email)
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Ensure FRONTEND_URL is set in settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000') # Default if not set
        reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"
        
        send_mail(
            'Password Reset',
            f'Click the following link to reset your password: {reset_url}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'Password reset email has been sent.',
            'email': email
        })

@extend_schema(
    summary="Confirm Password Reset",
    description="Allows a user to set a new password using a valid UID and token from the password reset email.",
    parameters=[
        OpenApiParameter(name='uid', location=OpenApiParameter.PATH, type=OpenApiTypes.STR, description='User ID from reset link.'),
        OpenApiParameter(name='token', location=OpenApiParameter.PATH, type=OpenApiTypes.STR, description='Token from reset link.')
    ],
    tags=['Users']
)
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uid, token):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # uid from path is already str, no need to decode if it's already base64 encoded by client or path converter handles it.
            # However, Django typically expects pk for get. If uid is the direct pk, use it.
            # If uid is base64 encoded string of pk, it needs decoding.
            # Assuming uid from path is the direct primary key as string for simplicity here, adjust if it's base64.
            user_pk_str = force_str(urlsafe_base64_decode(uid)) # Example if uid is base64
            user = CustomUser.objects.get(pk=user_pk_str)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist, Exception):
             # Added generic Exception if urlsafe_base64_decode fails due to padding etc.
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password has been reset successfully'})

@extend_schema(
    summary="Manage Staff Accounts (Admin)",
    description="Allows administrators to manage user accounts based on role hierarchy. Superadmins can manage all users, Admins can only manage frontdesk, kitchen, and delivery staff.",
    tags=['Users'] # Tag for the whole ViewSet
)
class StaffManagementViewSet(viewsets.ModelViewSet):
    serializer_class = StaffManagementSerializer
    permission_classes = [IsAdminOrSuperuser]

    def get_queryset(self):
        user = self.request.user
        
        # Superadmins can see all users except themselves
        if user.is_superuser and hasattr(user, 'role') and user.role == 'superadmin':
            return CustomUser.objects.all().exclude(pk=user.pk).order_by('id')
        
        # Admins can only see frontdesk, kitchen, and delivery staff (not other admins or superadmins)
        elif hasattr(user, 'role') and user.role == 'admin':
            return CustomUser.objects.filter(
                role__in=['frontdesk', 'kitchen', 'delivery']
            ).exclude(pk=user.pk).order_by('id')
        
        # If somehow they got through permission but don't have proper role, return empty
        return CustomUser.objects.none()
    
    def perform_create(self, serializer):
        # Check if the requesting user has permission to create this role
        user = self.request.user
        target_role = serializer.validated_data.get('role')
        
        # Only superadmins can create admin or superadmin users
        if target_role in ['admin', 'superadmin']:
            if not (user.is_superuser and hasattr(user, 'role') and user.role == 'superadmin'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Only superadmins can create admin or superadmin users.")
        
        # Admins can only create frontdesk, kitchen, and delivery staff
        if hasattr(user, 'role') and user.role == 'admin':
            if target_role not in ['frontdesk', 'kitchen', 'delivery']:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Admins can only create frontdesk, kitchen, and delivery staff.")
        
        serializer.save()
    
    def perform_update(self, serializer):
        # Check if the requesting user has permission to update this user
        user = self.request.user
        target_user = self.get_object()
        new_role = serializer.validated_data.get('role', target_user.role)
        
        # Only superadmins can modify admin or superadmin users
        if target_user.role in ['admin', 'superadmin'] or new_role in ['admin', 'superadmin']:
            if not (user.is_superuser and hasattr(user, 'role') and user.role == 'superadmin'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Only superadmins can modify admin or superadmin users.")
        
        # Admins can only modify frontdesk, kitchen, and delivery staff
        if hasattr(user, 'role') and user.role == 'admin':
            if target_user.role not in ['frontdesk', 'kitchen', 'delivery'] or new_role not in ['frontdesk', 'kitchen', 'delivery']:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Admins can only modify frontdesk, kitchen, and delivery staff.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # Check if the requesting user has permission to delete this user
        user = self.request.user
        
        # Only superadmins can delete admin or superadmin users
        if instance.role in ['admin', 'superadmin']:
            if not (user.is_superuser and hasattr(user, 'role') and user.role == 'superadmin'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Only superadmins can delete admin or superadmin users.")
        
        # Admins can only delete frontdesk, kitchen, and delivery staff
        if hasattr(user, 'role') and user.role == 'admin':
            if instance.role not in ['frontdesk', 'kitchen', 'delivery']:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Admins can only delete frontdesk, kitchen, and delivery staff.")
        
        instance.delete()

    # Add extend_schema for specific actions if default ModelViewSet descriptions are not sufficient
    @extend_schema(summary="Create Staff User (Admin)", tags=['Users'])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve Staff User (Admin)", tags=['Users'])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update Staff User (Admin)", tags=['Users'])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partially Update Staff User (Admin)", tags=['Users'])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete Staff User (Admin)", tags=['Users'])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

