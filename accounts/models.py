from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("phone_number is required")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("platform_role", "main_admin")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    class AccountState(models.TextChoices):
        UNCLAIMED = "unclaimed", "Unclaimed"
        VERIFIED = "verified", "Verified"

    class PlatformRole(models.TextChoices):
        NONE = "none", "None"
        SUPPORT = "support", "Support"
        MAIN_ADMIN = "main_admin", "Main admin"

    username = None
    phone_number = models.CharField(max_length=15, unique=True)
    account_state = models.CharField(
        max_length=20,
        choices=AccountState.choices,
        default=AccountState.UNCLAIMED,
    )
    platform_role = models.CharField(
        max_length=20,
        choices=PlatformRole.choices,
        default=PlatformRole.NONE,
    )
    email = models.EmailField(unique=True, null=True, blank=True)


    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.phone_number

class OtpCode(models.Model):
    """کد یک‌بارمصرف پیامکی برای ورود با OTP."""
    MAX_ATTEMPTS = 3
    TTL_MINUTES = 5

    phone_number = models.CharField(max_length=15, db_index=True)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def is_locked(self):
        return self.attempts >= self.MAX_ATTEMPTS

    def __str__(self):
        return f"{self.phone_number} ({'used' if self.is_used else 'active'})"