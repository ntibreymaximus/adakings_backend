from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class TokenObtainPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    access_expires_at = serializers.DateTimeField()
    refresh_expires_at = serializers.DateTimeField()
    user = serializers.DictField()


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    access_expires_at = serializers.DateTimeField()
    refresh_expires_at = serializers.DateTimeField()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = getattr(user, 'role', 'user')
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add expiration times
        refresh = RefreshToken(data['refresh'])
        access_token = refresh.access_token
        
        # Calculate expiration times
        access_expires_at = datetime.utcnow() + settings.ACCESS_TOKEN_LIFETIME
        refresh_expires_at = datetime.utcnow() + settings.REFRESH_TOKEN_LIFETIME
        
        # Add user info
        user_data = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': getattr(self.user, 'role', 'user'),
            'is_active': self.user.is_active,
            'is_staff': self.user.is_staff,
            'last_login': self.user.last_login,
            'date_joined': self.user.date_joined,
        }
        
        data.update({
            'access_expires_at': access_expires_at,
            'refresh_expires_at': refresh_expires_at,
            'user': user_data
        })
        
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            data = super().validate(attrs)
            
            # Calculate expiration times for the new tokens
            access_expires_at = datetime.utcnow() + settings.ACCESS_TOKEN_LIFETIME
            refresh_expires_at = datetime.utcnow() + settings.REFRESH_TOKEN_LIFETIME
            
            data.update({
                'access_expires_at': access_expires_at,
                'refresh_expires_at': refresh_expires_at,
            })
            
            return data
            
        except Exception as e:
            # Re-raise the exception to let the parent view handle it
            raise e


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    @extend_schema(
        summary="Obtain JWT Token Pair",
        description="Authenticate user and obtain access and refresh tokens with expiration information",
        responses={
            200: OpenApiResponse(
                response=TokenObtainPairResponseSerializer,
                description="Successfully authenticated"
            ),
            400: OpenApiResponse(description="Invalid credentials"),
            401: OpenApiResponse(description="Authentication failed"),
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                # Log successful login
                username = request.data.get('username', 'Unknown')
                logger.info(f"User {username} successfully authenticated")
                
                # Add helpful headers
                response['X-Token-Type'] = 'Bearer'
                response['X-Access-Token-Lifetime'] = str(settings.ACCESS_TOKEN_LIFETIME.total_seconds())
                response['X-Refresh-Token-Lifetime'] = str(settings.REFRESH_TOKEN_LIFETIME.total_seconds())
                
            return response
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return Response(
                {'error': 'Authentication failed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
    
    @extend_schema(
        summary="Refresh JWT Token",
        description="Refresh access token using refresh token with expiration information",
        responses={
            200: OpenApiResponse(
                response=TokenRefreshResponseSerializer,
                description="Successfully refreshed token"
            ),
            400: OpenApiResponse(description="Invalid refresh token"),
            401: OpenApiResponse(description="Token refresh failed"),
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                # Log successful token refresh
                logger.info("Token successfully refreshed")
                
                # Add helpful headers
                response['X-Token-Type'] = 'Bearer'
                response['X-Access-Token-Lifetime'] = str(settings.ACCESS_TOKEN_LIFETIME.total_seconds())
                response['X-Refresh-Token-Lifetime'] = str(settings.REFRESH_TOKEN_LIFETIME.total_seconds())
                
            return response
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return Response(
                {'error': 'Token refresh failed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
