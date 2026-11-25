from django.utils import timezone
from rest_framework import serializers

from appointments.services.create_booking import SlotTakenError
from catalog.models import Provider, Service


class CreateBookingSerializer(serializers.Serializer):
    provider = serializers.IntegerField()
    service = serializers.IntegerField()
    start_at = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(
        required=False, min_value=1
    )
    custom_values = serializers.JSONField(required=False, default=dict)
    addon_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=list,
    )

    def validate_start_at(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("زمان گذشته قابل رزرو نیست")
        return value

    def validate(self, data):
        try:
            provider = Provider.objects.get(id=data["provider"])
            service = Service.objects.get(id=data["service"])
        except (Provider.DoesNotExist, Service.DoesNotExist):
            raise serializers.ValidationError("ارائه‌دهنده یا خدمت پیدا نشد")
        if service not in provider.services.all():
            raise serializers.ValidationError("این ارائه‌دهنده این خدمت را نمی‌دهد")
        data["provider_obj"] = provider
        data["service_obj"] = service
        return data