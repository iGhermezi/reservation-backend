from rest_framework import serializers

from core.validators import validate_not_past, validate_within_31_days


class FreeSlotsQuerySerializer(serializers.Serializer):
    provider = serializers.IntegerField()
    service = serializers.IntegerField()
    duration_minutes = serializers.IntegerField(required=False, min_value=1)
    date = serializers.DateField(
        validators=[validate_not_past, validate_within_31_days]
    )
