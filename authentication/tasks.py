from celery import shared_task
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_sms_task(self, phone_number, message):
    """
    Celery task to send SMS using external SMS service
    """
    try:
        # SMS.uz API example
        url = "https://notify.eskiz.uz/api/message/sms/send"

        # Get token first (you should implement token refresh logic)
        token_url = "https://notify.eskiz.uz/api/auth/login"
        auth_data = {
            'email': settings.SMS_EMAIL,
            'password': settings.SMS_PASSWORD
        }

        # Get auth token
        auth_response = requests.post(token_url, data=auth_data, timeout=10)
        if auth_response.status_code != 200:
            raise Exception("Failed to get SMS auth token")

        token = auth_response.json().get('data', {}).get('token')

        # Send SMS
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        sms_data = {
            'mobile_phone': phone_number,
            'message': message,
            'from': '4546'  # Your SMS sender ID
        }

        response = requests.post(url, json=sms_data, headers=headers, timeout=10)

        if response.status_code == 200:
            logger.info(f"SMS sent successfully to {phone_number}")
            return {
                'success': True,
                'message': 'SMS sent successfully',
                'phone': phone_number
            }
        else:
            logger.error(f"SMS sending failed: {response.text}")
            raise Exception(f"SMS API error: {response.status_code}")

    except requests.exceptions.Timeout:
        logger.error(f"SMS sending timeout for {phone_number}")
        raise self.retry(countdown=60, exc=requests.exceptions.Timeout())

    except requests.exceptions.RequestException as e:
        logger.error(f"SMS sending network error: {str(e)}")
        raise self.retry(countdown=60, exc=e)

    except Exception as e:
        logger.error(f"SMS sending error: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=e)
        raise e


@shared_task
def cleanup_expired_otps():
    """
    Celery periodic task to cleanup expired OTP codes
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import OTPCode

    # Delete OTPs older than 10 minutes
    expired_time = timezone.now() - timedelta(minutes=10)
    deleted_count = OTPCode.objects.filter(created_at__lt=expired_time).delete()[0]

    logger.info(f"Cleaned up {deleted_count} expired OTP codes")
    return f"Cleaned up {deleted_count} expired OTP codes"