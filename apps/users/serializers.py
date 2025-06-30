# apps/users/serializers.py
from rest_framework import serializers
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser', 'is_active', 'date_joined')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label='Confirm password')

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password2', 'role')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name') # Add other fields as needed

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs

class StaffManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser', 'is_active')
        read_only_fields = ('id', 'username', 'email', 'date_joined', 'is_superuser') # Make some fields read-only for staff updates

