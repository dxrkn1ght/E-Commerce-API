from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    default_shipping_address = models.TextField(blank=True)
    is_phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.phone


class OTPVerification(models.Model):
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        """OTP kodining muddati tugaganligini tekshirish (5 daqiqa)"""
        return timezone.now() - self.created_at < timedelta(minutes=5)

    def __str__(self):
        return f"{self.phone} - {self.code}"