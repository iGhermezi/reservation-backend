from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment, AppointmentLog
from appointments.services.create_booking import SlotTakenError
from appointments.services.log import log_appointment
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

    expired_hold = False
    updated = None
    with transaction.atomic():
        locked = (
            Appointment.objects.select_for_update().get(pk=appointment.pk)
        )
        if locked.customer_id != by_user.id:
            raise RescheduleValidationError("این نوبت متعلق به شما نیست")

        now = timezone.now()
        if (
            locked.status == Appointment.Status.HELD
            and (locked.occupies_until is None or locked.occupies_until <= now)
        ):
            locked.status = Appointment.Status.EXPIRED
            locked.save(update_fields=["status", "updated_at"])
            expired_hold = True
        else:
            if locked.status not in RESCHEDULABLE_STATUSES:
                raise RescheduleValidationError(
                    f"نوبت در وضعیت {locked.get_status_display()} قابل تغییر زمان نیست"
                )
            if locked.reschedule_count >= 1:
                raise RescheduleValidationError("تغییر زمان فقط یک بار ممکن است")
            if new_start_at is None or timezone.is_naive(new_start_at):
                raise RescheduleValidationError(
                    "زمان جدید باید تاریخ و ساعت معتبر باشد"
                )
            if new_start_at < now:
                raise RescheduleValidationError("زمان گذشته قابل رزرو نیست")

            old_hours_before = (
                locked.start_at - now
            ).total_seconds() / 3600
            new_hours_before = (
                new_start_at - now
            ).total_seconds() / 3600
            if old_hours_before < 6 or new_hours_before < 6:
                raise RescheduleValidationError(
                    "تغییر زمان فقط تا ۶ ساعت قبل از شروع هر دو زمان ممکن است"
                )

            provider = Provider.objects.select_for_update().get(
                id=locked.provider_id
            )
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
            update_fields = [
                "start_at",
                "end_at",
                "reschedule_count",
                "status_reason",
                "updated_at",
            ]
            if locked.status == Appointment.Status.HELD:
                locked.occupies_until = now + timedelta(minutes=10)
                update_fields.append("occupies_until")
            locked.save(update_fields=update_fields)
            log_appointment(
                locked,
                AppointmentLog.Action.RESCHEDULED,
                actor=by_user,
                note=f"زمان جدید: {locked.start_at.isoformat()}",
            )
            updated = locked

    if expired_hold:
        raise RescheduleValidationError("مهلت نگهداری نوبت به پایان رسیده است")
    return updated