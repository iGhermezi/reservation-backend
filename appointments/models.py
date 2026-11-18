import uuid
from django.conf import settings
from django.db import models
from core.models import BaseModel


class Appointment(BaseModel):
    class Status(models.TextChoices):
        HELD = "held", "نگه داشته شده"
        PENDING_REVIEW = "pending_review", "در انتظار بررسی"
        AWAITING_REUPLOAD = "awaiting_reupload", "در انتظار اصلاح رسید"
        CONFIRMED = "confirmed", "تایید شده"
        CANCELLED = "cancelled", "لغو شده"
        EXPIRED = "expired", "منقضی شده"
        COMPLETED = "completed", "تکمیل شده"
        NO_SHOW = "no_show", "عدم حضور"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    business = models.ForeignKey(
        "businesses.Business", on_delete=models.PROTECT, related_name="appointments"
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments"
    )
    provider = models.ForeignKey(
        "catalog.Provider", on_delete=models.PROTECT, related_name="appointments"
    )
    service = models.ForeignKey(
        "catalog.Service", on_delete=models.PROTECT, related_name="appointments"
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    price_final = models.DecimalField(max_digits=10, decimal_places=0)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.HELD
    )
    occupies_until = models.DateTimeField(null=True, blank=True)
    review_deadline_at = models.DateTimeField(null=True, blank=True)
    receipt_reject_count = models.PositiveSmallIntegerField(default=0)
    reschedule_count = models.PositiveSmallIntegerField(default=0)
    status_reason = models.CharField(max_length=200, blank=True, default="")
    created_via = models.CharField(max_length=20, default="customer")
    created_by_membership = models.ForeignKey(
        "businesses.Membership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_appointments",
    )
    custom_values = models.JSONField(default=dict, blank=True)
    name_snapshot = models.CharField(max_length=100, blank=True, default="")
    phone_snapshot = models.CharField(max_length=15, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(
                fields=["provider", "start_at"],
                name="appt_provider_start_idx",
            ),
            models.Index(
                fields=["business", "start_at"],
                name="appt_business_start_idx",
            ),
        ]

    def __str__(self):
        return f"{self.public_id} - {self.status}"
