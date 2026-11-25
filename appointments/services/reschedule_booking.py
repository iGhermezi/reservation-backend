from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment
from appointments.services.create_booking import SlotTakenError
from catalog.models import Provider
from scheduling.services.free_slots import get_free_slots


class RescheduleValidationError(Exception):
    pass


RESCHEDULABLE_STATUSES = (
    Appointment.Status.HELD,
    Appointment.Status.PENDING_REVIEW,
    Appointment.Status.AWAITING_REUPLOAD,
    Appointment.Status.CONFIRMED,
)


def reschedule_appointment(appointment, by_user, new_start_at):
    """زمان نوبت رو عوض کن؛ فقط یک بار و تا ۶ ساعت قبل از شروع."""
    if appointment.customer_id != by_user.id:
        raise RescheduleValidationError("این نوبت متعلق به شما نیست")
    if new_start_at is None or timezone.is_naive(new_start_at):
        raise RescheduleValidationError("زمان جدید باید تاریخ و ساعت معتبر باشد")
    if new_start_at < timezone.now():
        raise RescheduleValidationError("زمان گذشته قابل رزرو نیست")

    with transaction.atomic():
        locked = (
            Appointment.objects.select_for_update().get(pk=appointment.pk)
        )
        if locked.status not in RESCHEDULABLE_STATUSES:
            raise RescheduleValidationError(
                f"نوبت در وضعیت {locked.get_status_display()} قابل تغییر زمان نیست"
            )
        if locked.reschedule_count >= 1:
            raise RescheduleValidationError("تغییر زمان فقط یک بار ممکن است")

        hours_before = (locked.start_at - timezone.now()).total_seconds() / 3600
        if hours_before < 6:
            raise RescheduleValidationError(
                "تغییر زمان فقط تا ۶ ساعت قبل از شروع نوبت ممکن است"
            )

        provider = Provider.objects.select_for_update().get(id=locked.provider_id)
        new_end_at = new_start_at + timedelta(minutes=locked.duration_minutes)

        local = timezone.localtime(new_start_at)
        free = get_free_slots(
            provider,
            locked.service,
            local.date(),
            duration_minutes=locked.duration_minutes,
            exclude_appointment_id=locked.pk,
        )
        if local.time() not in free:
            raise SlotTakenError("این ساعت آزاد نیست")

        locked.start_at = new_start_at
        locked.end_at = new_end_at
        locked.reschedule_count += 1
        locked.status_reason = "تغییر زمان توسط مشتری"
        locked.save(update_fields=[
            "start_at", "end_at", "reschedule_count", "status_reason",
        ])
        return locked