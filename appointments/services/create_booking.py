from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment
from appointments.services.custom_fields import (
    calculate_final_price,
    validate_custom_values,
)
from catalog.models import Provider
from scheduling.services.free_slots import get_free_slots
from scheduling.services.duration import resolve_duration


class SlotTakenError(Exception):
    pass


class BookingValidationError(Exception):
    pass


def _resolve_duration(service, duration_minutes):
    try:
        return resolve_duration(service, duration_minutes)
    except ValueError as e:
        raise BookingValidationError(str(e))


def create_booking(
    *,
    customer,
    provider_id,
    service,
    start_at,
    duration_minutes=None,
    custom_values=None,
    addon_ids=None,
):
    """یه نوبت نگه‌داشته‌شده بساز؛ اگه ساعت گرفته شده باشه خطا می‌ده."""
    if start_at is None or timezone.is_naive(start_at):
        raise BookingValidationError("زمان شروع باید تاریخ و ساعت معتبر باشد")
    if start_at < timezone.now():
        raise BookingValidationError("زمان گذشته قابل رزرو نیست")

    duration = _resolve_duration(service, duration_minutes)
    end_at = start_at + timedelta(minutes=duration)

    try:
        validated_values = validate_custom_values(service, custom_values)
    except ValueError as e:
        raise BookingValidationError(str(e))

    with transaction.atomic():
        provider = Provider.objects.select_for_update().get(id=provider_id)

        if provider.business_id != service.business_id:
            raise BookingValidationError("ارائه‌دهنده متعلق به کسب‌وکار این خدمت نیست")
        if not service.providers.filter(id=provider.id).exists():
            raise BookingValidationError("این ارائه‌دهنده این خدمت را نمی‌دهد")
        if not provider.is_active:
            raise BookingValidationError("ارائه‌دهنده غیرفعال است")
        if not service.is_active:
            raise BookingValidationError("خدمت غیرفعال است")
        if not service.business.is_active:
            raise BookingValidationError("کسب‌وکار غیرفعال است")

        _expire_old_holds(provider)

        local = timezone.localtime(start_at)
        free = get_free_slots(provider, service, local.date(), duration_minutes=duration)
        if local.time() not in free:
            raise SlotTakenError("این ساعت آزاد نیست")

        try:
            price_final = calculate_final_price(
                service, validated_values, addon_ids=addon_ids
            )
        except ValueError as e:
            raise BookingValidationError(str(e))

        return Appointment.objects.create(
            business_id=service.business_id,
            customer=customer,
            provider=provider,
            service=service,
            start_at=start_at,
            end_at=end_at,
            duration_minutes=duration,
            price_final=price_final,
            deposit_amount=service.deposit_amount or 0,
            status=Appointment.Status.HELD,
            occupies_until=timezone.now() + timedelta(minutes=10),
            custom_values=validated_values,
        )


def _expire_old_holds(provider):
    """هولدهای منقضی این ارائه‌دهنده رو آزاد کن."""
    now = timezone.now()
    Appointment.objects.filter(
        provider=provider,
        status=Appointment.Status.HELD,
        occupies_until__lt=now,
    ).update(status=Appointment.Status.EXPIRED)