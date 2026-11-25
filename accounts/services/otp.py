import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from accounts.models import OtpCode, User
from accounts.services.sms import LogProvider


class OtpError(Exception):
    pass


class OtpRateLimitError(OtpError):
    pass


def _random_code():
    return "".join(secrets.choice("0123456789") for _ in range(6))


def request_otp(phone_number, ip_address=None, provider=None):
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
    OtpCode.objects.create(
        phone_number=phone_number,
        code_hash=make_password(code),
        expires_at=now + timedelta(minutes=OtpCode.TTL_MINUTES),
        ip_address=ip_address,
    )
    (provider or LogProvider()).send(phone_number, code)
    return code


def verify_otp(phone_number, code):
    otp = (
        OtpCode.objects.filter(phone_number=phone_number, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if otp is None:
        raise OtpError("کدی برای این شماره پیدا نشد")
    if otp.is_expired():
        raise OtpError("کد منقضی شده است")
    if otp.is_locked():
        raise OtpError("تعداد تلاش اشتباه زیاد است")
    if not check_password(code, otp.code_hash):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        raise OtpError("کد اشتباه است")

    otp.is_used = True
    otp.save(update_fields=["is_used"])
    user, _ = User.objects.get_or_create(phone_number=phone_number)
    if user.account_state != User.AccountState.VERIFIED:
        user.account_state = User.AccountState.VERIFIED
        user.save(update_fields=["account_state"])
    return user