from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q, UniqueConstraint

from core.models import BaseModel


class Business(BaseModel):
    class DeactivatedBy(models.TextChoices):
        OWNER = "owner", "Owner"
        SUPPORT = "support", "Support"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    deactivated_by = models.CharField(
        max_length=20,
        choices=DeactivatedBy.choices,
        null=True,
        blank=True,
    )
    deactivated_reason = models.TextField(blank=True, default="")
    deactivated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["city", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.slug})"

PERMISSIONS = (
    "appointments.view",
    "appointments.create_manual",
    "appointments.manage",
    "appointments.record_attendance",
    "appointments.view_log",
    "receipts.review",
    "customers.view",
    "services.manage",
    "providers.manage",
    "schedule.manage",
    "extras.manage",
    "page.edit",
)

# قالب‌های آماده دسترسی کارورز
STAFF_PERMISSION_TEMPLATES = {
    "secretary": ["appointments.view", "appointments.create_manual", "appointments.manage"],
    "viewer": ["appointments.view"],
    "page_manager": ["appointments.view", "page.edit"],
    "full": list(PERMISSIONS),
}


class Membership(BaseModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        STAFF = "staff", "Staff"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF,
    )
    permissions = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_memberships",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "business"],
                name="unique_membership",
            ),
            UniqueConstraint(
                fields=["business"],
                condition=Q(role="owner", is_active=True),
                name="unique_active_owner_per_business",
            ),
        ]
        indexes = [
            models.Index(fields=["business", "is_active"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.business.slug} ({self.role})"

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER and self.is_active

    def has_permission(self, code):
        if not self.is_active:
            return False
        if self.role == self.Role.OWNER:
            return True
        return code in self.permissions