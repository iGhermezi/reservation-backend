from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment
from catalog.models import Provider
from scheduling.services.free_slots import get_free_slots


class SlotTakenError(Exception):
    pass


def create_booking(*, customer, provider_id, service, start_at):
    """یه نوبت نگه‌داشته‌شده بساز؛ اگه ساعت گرفته شده باشه خطا می‌ده."""
    duration = service.duration_minutes or service.min_minutes
    end_at = start_at + timedelta(minutes=duration)

    with transaction.atomic():
        provider = Provider.objects.select_for_update().get(id=provider_id)
        _expire_old_holds(provider)
        free = get_free_slots(provider, service, start_at.date())
        if start_at.time() not in free:
            raise SlotTakenError("این ساعت آزاد نیست")
        return Appointment.objects.create(
            business=service.business,
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

