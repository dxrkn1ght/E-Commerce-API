import random
import string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def generate_verification_code(length=6):
    """Generate random verification code"""
    return ''.join(random.choices(string.digits, k=length))


def send_sms_code(phone, message):
    """
    Send SMS using SMS service provider
    This is a generic implementation - you need to integrate with actual SMS provider
    """
    try:
        # Example integration with Twilio
        if hasattr(settings, 'TWILIO_ACCOUNT_SID'):
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            message = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )

            logger.info(f"SMS sent successfully to {phone}. SID: {message.sid}")
            return True

        # Example integration with custom SMS API
        elif hasattr(settings, 'SMS_API_URL'):
            payload = {
                'phone': phone,
                'message': message,
                'api_key': settings.SMS_API_KEY
            }

            response = requests.post(
                settings.SMS_API_URL,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"SMS sent successfully to {phone}")
                    return True
                else:
                    logger.error(f"SMS API error: {result.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"SMS API HTTP error: {response.status_code}")
                return False

        # Example integration with Eskiz.uz (Uzbekistan SMS provider)
        elif hasattr(settings, 'ESKIZ_EMAIL'):
            # First, get token
            auth_response = requests.post(
                'https://notify.eskiz.uz/api/auth/login',
                data={
                    'email': settings.ESKIZ_EMAIL,
                    'password': settings.ESKIZ_PASSWORD
                }
            )

            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                token = auth_data['data']['token']

                # Send SMS
                sms_response = requests.post(
                    'https://notify.eskiz.uz/api/message/sms/send',
                    headers={'Authorization': f'Bearer {token}'},
                    data={
                        'mobile_phone': phone,
                        'message': message,
                        'from': '4546'  # Eskiz default sender
                    }
                )

                if sms_response.status_code == 200:
                    logger.info(f"SMS sent successfully to {phone} via Eskiz")
                    return True
                else:
                    logger.error(f"Eskiz SMS error: {sms_response.text}")
                    return False
            else:
                logger.error(f"Eskiz auth error: {auth_response.text}")
                return False

        # Development mode - just log the message
        else:
            logger.info(f"Development mode - SMS to {phone}: {message}")
            print(f"SMS to {phone}: {message}")  # For development
            return True

    except Exception as e:
        logger.error(f"SMS sending failed: {str(e)}")
        return False


def format_phone_number(phone):
    """
    Format phone number to international format
    """
    # Remove all non-digit characters
    phone = ''.join(filter(str.isdigit, phone))

    # Add +998 prefix for Uzbekistan numbers if not present
    if phone.startswith('998'):
        phone = '+' + phone
    elif phone.startswith('9') and len(phone) == 9:
        phone = '+998' + phone
    elif not phone.startswith('+'):
        phone = '+' + phone

    return phone


def validate_phone_number(phone):
    """
    Validate phone number format
    """
    phone = format_phone_number(phone)

    # Basic validation - should start with + and have 10-15 digits
    if phone.startswith('+') and len(phone) >= 10 and len(phone) <= 16:
        digits = phone[1:]
        if digits.isdigit():
            return True

    return False


def mask_phone_number(phone):
    """
    Mask phone number for display (e.g., +998*****1234)
    """
    if len(phone) < 8:
        return phone

    return phone[:4] + '*' * (len(phone) - 8) + phone[-4:]


# SMS Templates
SMS_TEMPLATES = {
    'verification': "Tasdiqlash kodi: {code}. Bu kodni hech kimga bermang!",
    'password_reset': "Parolni tiklash kodi: {code}. Bu kodni hech kimga bermang!",
    'welcome': "Xush kelibsiz! Hisobingiz muvaffaqiyatli yaratildi.",
    'order_confirmation': "Buyurtmangiz #{order_number} qabul qilindi. Jami: {total} so'm"
}


def get_sms_template(template_name, **kwargs):
    """
    Get formatted SMS template
    """
    template = SMS_TEMPLATES.get(template_name, '')
    if template:
        return template.format(**kwargs)
    return ''


# Rate limiting for SMS sending
SMS_RATE_LIMIT = {
    'max_per_phone_per_hour': 5,
    'max_per_phone_per_day': 20,
    'max_per_ip_per_hour': 50
}


def check_sms_rate_limit(phone, ip_address=None):
    """
    Check if SMS sending is within rate limits
    """
    from django.core.cache import cache
    import time

    current_time = int(time.time())
    hour_key = f"sms_rate_{phone}_{current_time // 3600}"
    day_key = f"sms_rate_day_{phone}_{current_time // 86400}"

    # Check hourly limit
    hourly_count = cache.get(hour_key, 0)
    if hourly_count >= SMS_RATE_LIMIT['max_per_phone_per_hour']:
        return False, "Hourly limit exceeded"

    # Check daily limit
    daily_count = cache.get(day_key, 0)
    if daily_count >= SMS_RATE_LIMIT['max_per_phone_per_day']:
        return False, "Daily limit exceeded"

    # Check IP limit if provided
    if ip_address:
        ip_hour_key = f"sms_rate_ip_{ip_address}_{current_time // 3600}"
        ip_hourly_count = cache.get(ip_hour_key, 0)
        if ip_hourly_count >= SMS_RATE_LIMIT['max_per_ip_per_hour']:
            return False, "IP hourly limit exceeded"

    return True, "OK"


def increment_sms_rate_limit(phone, ip_address=None):
    """
    Increment SMS rate limit counters
    """
    from django.core.cache import cache
    import time

    current_time = int(time.time())
    hour_key = f"sms_rate_{phone}_{current_time // 3600}"
    day_key = f"sms_rate_day_{phone}_{current_time // 86400}"

    # Increment counters
    cache.set(hour_key, cache.get(hour_key, 0) + 1, timeout=3600)
    cache.set(day_key, cache.get(day_key, 0) + 1, timeout=86400)

    if ip_address:
        ip_hour_key = f"sms_rate_ip_{ip_address}_{current_time // 3600}"
        cache.set(ip_hour_key, cache.get(ip_hour_key, 0) + 1, timeout=3600)