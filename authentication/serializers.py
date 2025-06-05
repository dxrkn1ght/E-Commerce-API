from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .models import OTPVerification
import re

User = get_user_model()


class AuthorizeSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(required=False)

    def validate_phone(self, value):
        # Telefon raqam formatini tekshirish
        if not re.match(r'^\+\d{10,15}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        return value


class VerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()
    password = serializers.CharField(required=False)
    name = serializers.CharField(required=False)

    def validate_phone(self, value):
        if not re.match(r'^\+\d{10,15}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        return value


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')

        if phone and password:
            user = authenticate(username=phone, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_phone_verified:
                raise serializers.ValidationError("Phone number not verified")
        else:
            raise serializers.ValidationError("Phone and password required")

        data['user'] = user
        return data


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        if not re.match(r'^\+\d{10,15}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("User with this phone number not found")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()
    new_password = serializers.CharField()

    def validate_phone(self, value):
        if not re.match(r'^\+\d{10,15}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'first_name', 'last_name', 'email',
                  'default_shipping_address', 'date_joined']
        read_only_fields = ['id', 'phone', 'date_joined']
