from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment
from catalog.models import Provider
from scheduling.services.free_slots import get_free_slots
from scheduling.services.overlap import overlaps


class SlotTakenError(Exception):
    pass


class BookingValidationError(Exception):
    pass


def _resolve_duration(service, duration_minutes):
    """مدت نهایی رزرو رو مشخص کن و اعتبارسنجی کن."""
    if service.duration_type == service.DurationType.FIXED:
        return service.duration_minutes

    duration = duration_minutes or service.min_minutes
    if duration < service.min_minutes or duration > service.max_minutes:
        raise BookingValidationError("مدت باید بین حداقل و حداکثر خدمت باشد")
    step = service.step_minutes or 15
    if (duration - service.min_minutes) % step != 0:
        raise BookingValidationError("مدت باید مضرب گام خدمت باشد")
    return duration


def create_booking(*, customer, provider_id, service, start_at, duration_minutes=None):
    """یه نوبت نگه‌داشته‌شده بساز؛ اگه ساعت گرفته شده باشه خطا می‌ده."""
    if start_at is None or timezone.is_naive(start_at):
        raise BookingValidationError("زمان شروع باید تاریخ و ساعت معتبر باشد")
    if start_at < timezone.now():
        raise BookingValidationError("زمان گذشته قابل رزرو نیست")

    duration = _resolve_duration(service, duration_minutes)
    end_at = start_at + timedelta(minutes=duration)

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

        if service.capacity == 1:
            free = get_free_slots(
                provider, service, start_at.date(), duration_minutes=duration
            )
            if start_at.time() not in free:
                raise SlotTakenError("این ساعت آزاد نیست")
        else:
            active_statuses = ["held", "pending_review", "awaiting_reupload", "confirmed"]
            count = 0
            for appt in provider.appointments.filter(
                status__in=active_statuses,
            ).exclude(status="held", occupies_until__lt=timezone.now()):
                appt_start = timezone.localtime(appt.start_at)
                appt_end = timezone.localtime(appt.end_at)
                if overlaps(start_at, end_at, appt_start, appt_end):
                    count += 1
            if count >= service.capacity:
                raise SlotTakenError("ظرفیت این ساعت پر شده است")

        return Appointment.objects.create(
            business_id=service.business_id,
            customer=customer,
            provider=provider,
            service=service,
            start_at=start_at,
            end_at=end_at,
            duration_minutes=duration,
            price_final=service.price,
            deposit_amount=service.deposit_amount or 0,
            status=Appointment.Status.HELD,
            occupies_until=timezone.now() + timedelta(minutes=10),
        )


def _expire_old_holds(provider):
    """هولدهای منقضی این ارائه‌دهنده رو آزاد کن."""
    now = timezone.now()
    Appointment.objects.filter(
        provider=provider,
        status=Appointment.Status.HELD,
        occupies_until__lt=now,
    ).update(status=Appointment.Status.EXPIRED)
