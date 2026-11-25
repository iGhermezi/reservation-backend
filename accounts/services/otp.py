import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from accounts.models import OtpCode, User
from accounts.services.phone import normalize_phone
from accounts.services.sms import LogProvider


class OtpError(Exception):
    pass


class OtpRateLimitError(OtpError):
    pass


def _random_code():
    return "".join(secrets.choice("0123456789") for _ in range(6))


def request_otp(phone_number, ip_address=None, provider=None):
    phone_number = normalize_phone(phone_number)
    if provider is None:
        if not settings.DEBUG:
            raise OtpError("SMS provider not configured")
        provider = LogProvider()
    elif isinstance(provider, LogProvider) and not settings.DEBUG:
        raise OtpError("SMS provider not configured")

    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)
    if OtpCode.objects.filter(
        phone_number=phone_number, created_at__gte=one_hour_ago
    ).count() >= 5:
        raise OtpRateLimitError("تعداد درخواست کد برای این شماره زیاد است")
    if ip_address and OtpCode.objects.filter(
        ip_address=ip_address, created_at__gte=one_hour_ago
    ).count() >= 20:
        raise OtpRateLimitError("تعداد درخواست کد از این IP زیاد است")

    # کدهای قبلی استفاده‌نشده همین شماره رو باطل کن — فقط آخرین کد معتبره
    OtpCode.objects.filter(
        phone_number=phone_number, is_used=False
    ).update(is_used=True)

    code = _random_code()
    otp = OtpCode.objects.create(
        phone_number=phone_number,
        code_hash=make_password(code),
        expires_at=now + timedelta(minutes=OtpCode.TTL_MINUTES),
        ip_address=ip_address,
    )
    try:
        provider.send(phone_number, code)
    except Exception as exc:
        otp.delete()
        raise OtpError("SMS delivery failed") from exc
    return code


def verify_otp(phone_number, code):
    phone_number = normalize_phone(phone_number)
    error_message = None
    user = None

    with transaction.atomic():
        otp = (
            OtpCode.objects.select_for_update()
            .filter(phone_number=phone_number, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if otp is None:
            error_message = "کدی برای این شماره پیدا نشد"
        elif otp.is_expired():
            error_message = "کد منقضی شده است"
        elif otp.is_locked():
            error_message = "تعداد تلاش اشتباه زیاد است"
        elif not check_password(code, otp.code_hash):
            OtpCode.objects.filter(pk=otp.pk).update(
                attempts=F("attempts") + 1
            )
            error_message = "کد اشتباه است"
        else:
            user, _ = User.objects.get_or_create(phone_number=phone_number)
            if not user.is_active:
                error_message = "این حساب غیرفعال است"
            else:
                otp.is_used = True
                otp.save(update_fields=["is_used"])
                if user.account_state != User.AccountState.VERIFIED:
                    user.set_unusable_password()
                    user.account_state = User.AccountState.VERIFIED
                    user.save(update_fields=["password", "account_state"])

    if error_message:
        raise OtpError(error_message)
    return user