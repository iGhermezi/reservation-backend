from django.conf import settings
from django.db import models
from core.models import BaseModel

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
            raise models.ValidationError(
                "Flexible duration is only allowed with capacity 1."
            )
        if self.duration_type == self.DurationType.FIXED and not self.duration_minutes:
            raise models.ValidationError(
                "Fixed service needs duration_minutes."
            )
        if self.duration_type == self.DurationType.FLEXIBLE and not (
            self.min_minutes and self.max_minutes
        ):
            raise models.ValidationError(
                "Flexible service needs min_minutes and max_minutes."
            )



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
