from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings
from .utils import send_sms_code, generate_verification_code
from .tasks import send_sms_task
import random
import string


@api_view(['POST'])
@permission_classes([AllowAny])
def authorize(request):
    """Request SMS verification code"""
    phone = request.data.get('phone')
    password = request.data.get('password')

    if not phone:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Phone number is required'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    # Generate verification code
    code = generate_verification_code()

    # Store code in cache with 5 minutes expiry
    cache_key = f"sms_code_{phone}"
    cache.set(cache_key, {
        'code': code,
        'password': password,
        'attempts': 0
    }, timeout=300)  # 5 minutes

    # Send SMS using Celery task
    send_sms_task.delay(phone, f"Your verification code is: {code}")

    return Response({
        'success': True,
        'message': f'Verification code sent to {phone}'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_code(request):
    """Verify SMS code and register/login user"""
    phone = request.data.get('phone')
    code = request.data.get('code')
    password = request.data.get('password')
    name = request.data.get('name')

    if not phone or not code:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Phone number and code are required'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    # Get code from cache
    cache_key = f"sms_code_{phone}"
    cached_data = cache.get(cache_key)

    if not cached_data:
        return Response({
            'success': False,
            'error': {
                'code': 'CODE_EXPIRED',
                'message': 'Verification code has expired'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check attempts
    if cached_data.get('attempts', 0) >= 3:
        cache.delete(cache_key)
        return Response({
            'success': False,
            'error': {
                'code': 'TOO_MANY_ATTEMPTS',
                'message': 'Too many failed attempts. Please request a new code.'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verify code
    if cached_data['code'] != code:
        cached_data['attempts'] = cached_data.get('attempts', 0) + 1
        cache.set(cache_key, cached_data, timeout=300)

        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_CODE',
                'message': 'Invalid verification code'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    # Code is valid, clear cache
    cache.delete(cache_key)

    # Check if user exists
    try:
        user_profile = UserProfile.objects.get(phone=phone)
        user = user_profile.user

        # If password provided, this is login attempt
        if password:
            if not user.check_password(password):
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_CREDENTIALS',
                        'message': 'Invalid password'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)

    except UserProfile.DoesNotExist:
        # New user registration
        if not password or not name:
            return Response({
                'success': False,
                'error': {
                    'code': 'REGISTRATION_DATA_REQUIRED',
                    'message': 'Password and name are required for registration'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new user
        username = phone  # Use phone as username
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=name.split()[0] if name else '',
            last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
        )

        # Create user profile
        user_profile = UserProfile.objects.create(
            user=user,
            phone=phone,
            name=name
        )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    return Response({
        'success': True,
        'data': {
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'expires_in': settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login with phone and password"""
    phone = request.data.get('phone')
    password = request.data.get('password')

    if not phone or not password:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Phone number and password are required'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_profile = UserProfile.objects.get(phone=phone)
        user = user_profile.user

        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'success': True,
                'data': {
                    'access_token': str(access_token),
                    'refresh_token': str(refresh),
                    'expires_in': settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
                }
            })
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid phone number or password'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

    except UserProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid phone number or password'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout and blacklist refresh token"""
    refresh_token = request.data.get('refresh_token')

    if not refresh_token:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Refresh token is required'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({
            'success': True,
            'message': 'Successfully logged out'
        })
    except TokenError:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid refresh token'
            }
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh access token"""
    refresh_token = request.data.get('refresh_token')

    if not refresh_token:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Refresh token is required'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token

        return Response({
            'success': True,
            'data': {
                'access_token': str(access_token),
                'expires_in': settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
            }
        })
    except TokenError:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid refresh token'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Request password reset SMS"""
    phone = request.data.get('phone')

    if not phone:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Phone number is required'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_profile = UserProfile.objects.get(phone=phone)

        # Generate verification code
        code = generate_verification_code()

        # Store code in cache
        cache_key = f"reset_code_{phone}"
        cache.set(cache_key, {
            'code': code,
            'attempts': 0
        }, timeout=600)  # 10 minutes for password reset

        # Send SMS
        send_sms_task.delay(phone, f"Your password reset code is: {code}")

        return Response({
            'success': True,
            'message': f'Password reset code sent to {phone}'
        })

    except UserProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User with this phone number not found'
            }
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password after verification"""
    phone = request.data.get('phone')
    code = request.data.get('code')
    new_password = request.data.get('new_password')

    if not phone or not code or not new_password:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Phone number, code and new password are required'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    # Get code from cache
    cache_key = f"reset_code_{phone}"
    cached_data = cache.get(cache_key)

    if not cached_data:
        return Response({
            'success': False,
            'error': {
                'code': 'CODE_EXPIRED',
                'message': 'Reset code has expired'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check attempts
    if cached_data.get('attempts', 0) >= 3:
        cache.delete(cache_key)
        return Response({
            'success': False,
            'error': {
                'code': 'TOO_MANY_ATTEMPTS',
                'message': 'Too many failed attempts. Please request a new code.'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verify code
    if cached_data['code'] != code:
        cached_data['attempts'] = cached_data.get('attempts', 0) + 1
        cache.set(cache_key, cached_data, timeout=600)

        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_CODE',
                'message': 'Invalid reset code'
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_profile = UserProfile.objects.get(phone=phone)
        user = user_profile.user

        # Update password
        user.set_password(new_password)
        user.save()

        # Clear cache
        cache.delete(cache_key)

        return Response({
            'success': True,
            'message': 'Password reset successful'
        })

    except UserProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User not found'
            }
        }, status=status.HTTP_404_NOT_FOUND)