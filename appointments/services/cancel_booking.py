from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment


class CancelValidationError(Exception):
    pass


CANCELLABLE_STATUSES = (
    Appointment.Status.HELD,
    Appointment.Status.PENDING_REVIEW,
    Appointment.Status.AWAITING_REUPLOAD,
    Appointment.Status.CONFIRMED,
)


def refund_rate_for(start_at, now=None):
    """نرخ استرداد بیعانه بر اساس فاصله تا شروع نوبت."""
    now = now or timezone.now()
    hours_before = (start_at - now).total_seconds() / 3600
    if hours_before > 24:
        return Decimal("0.85")
    if hours_before >= 6:
        return Decimal("0.50")
    return Decimal("0")


def cancel_appointment(appointment, by_user):
    """نوبت مشتری رو لغو کن؛ دیکشنری با نرخ و مبلغ استرداد برمی‌گردونه."""
    if appointment.customer_id != by_user.id:
        raise CancelValidationError("این نوبت متعلق به شما نیست")

    with transaction.atomic():
        locked = (
            Appointment.objects.select_for_update().get(pk=appointment.pk)
        )
        if locked.status not in CANCELLABLE_STATUSES:
            raise CancelValidationError(
                f"نوبت در وضعیت {locked.get_status_display()} قابل لغو نیست"
            )

        rate = refund_rate_for(locked.start_at)
        refund_amount = locked.deposit_amount * rate

        locked.status = Appointment.Status.CANCELLED
        locked.status_reason = (
            f"لغو توسط مشتری؛ استرداد {int(rate * 100)}٪ بیعانه"
        )
        locked.occupies_until = None
        locked.save(update_fields=["status", "status_reason", "occupies_until"])

        return {
            "appointment": locked,
            "refund_rate": rate,
            "refund_amount": refund_amount,
        }