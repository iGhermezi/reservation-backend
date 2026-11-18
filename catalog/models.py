from django.conf import settings
from django.db import models
from core.models import BaseModel
from django.core.exceptions import ValidationError



class Service(BaseModel):
    class DurationType(models.TextChoices):
        FIXED = "fixed", "ثابت"
        FLEXIBLE = "flexible", "متغیر"

    business = models.ForeignKey(
        "businesses.Business",
        on_delete=models.CASCADE,
        related_name="services",
    )

    providers = models.ManyToManyField(
    "Provider",
    related_name="services",
    blank=True,
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=0)
    duration_type = models.CharField(
        max_length=20,
        choices=DurationType.choices,
        default=DurationType.FIXED,
    )
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    min_minutes = models.PositiveIntegerField(null=True, blank=True)
    max_minutes = models.PositiveIntegerField(null=True, blank=True)
    step_minutes = models.PositiveIntegerField(null=True, blank=True, default=15)
    deposit_amount = models.DecimalField(
        max_digits=10, decimal_places=0, null=True, blank=True
    )
    capacity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "name"],
                name="unique_service_name_per_business",
            )
        ]

    def clean(self):
        super().clean()
        if self.duration_type == self.DurationType.FLEXIBLE and self.capacity > 1:
            raise ValidationError(
                "Flexible duration is only allowed with capacity 1."
            )
        if self.duration_type == self.DurationType.FIXED and not self.duration_minutes:
            raise ValidationError(
                "Fixed service needs duration_minutes."
            )
        if self.duration_type == self.DurationType.FLEXIBLE and not (
            self.min_minutes and self.max_minutes
        ):
            raise ValidationError(
                "Flexible service needs min_minutes and max_minutes."
            )
        if (
            self.duration_type == self.DurationType.FLEXIBLE
            and self.min_minutes is not None
            and self.max_minutes is not None
            and self.min_minutes > self.max_minutes
        ):
            raise ValidationError("min_minutes must be <= max_minutes.")
        if self.deposit_amount is not None and self.price is not None and self.deposit_amount > self.price:
            raise ValidationError("deposit_amount must be <= price.")


class Provider(BaseModel):
    business = models.ForeignKey(
        "businesses.Business",
        on_delete=models.CASCADE,
        related_name="providers",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="provider_profiles",
    )
    display_name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.display_name



class WorkingHour(BaseModel):
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="working_hours",
    )
    weekday = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def clean(self):
        super().clean()
        if self.weekday is not None and not 0 <= self.weekday <= 6:
            raise ValidationError("weekday must be between 0 and 6.")
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.start_time >= self.end_time
        ):
            raise ValidationError("start_time must be before end_time.")

    def __str__(self):
        return f"{self.provider.display_name} - {self.weekday}: {self.start_time} to {self.end_time}"



class TimeOff(BaseModel):
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="time_offs",
    )
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True, default="")

    def clean(self):
        super().clean()
        if (self.start_time is None) != (self.end_time is None):
            raise ValidationError("start_time and end_time must both be set or empty.")
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.start_time >= self.end_time
        ):
            raise ValidationError("start_time must be before end_time.")

    def __str__(self):
        return f"{self.provider.display_name} - {self.date}"




class CustomFieldDefinition(BaseModel):
    class FieldType(models.TextChoices):
        TEXT = "text", "متن"
        NUMBER = "number", "عدد"
        CHOICE = "choice", "انتخابی"
        BOOLEAN = "boolean", "تیک"

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="custom_fields",
    )
    key = models.SlugField(max_length=50)
    label = models.CharField(max_length=100)
    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT,
    )
    is_required = models.BooleanField(default=False)
    choices = models.JSONField(default=list, blank=True)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=0, null=True, blank=True
    )

    def __str__(self):
        return f"{self.service.name} - {self.label}"




class ServiceAddon(BaseModel):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="addons",
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.service.name} - {self.name}"
