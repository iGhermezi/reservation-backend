from datetime import date

from rest_framework import serializers


def validate_not_past(value):
    """تاریخ نباید گذشته باشه."""
    if value < date.today():
        raise serializers.ValidationError("تاریخ گذشته قابل رزرو نیست")
    return value


def validate_within_31_days(value):
    """تاریخ حداکثر ۳۱ روز آینده باشه."""
    if (value - date.today()).days > 31:
        raise serializers.ValidationError("حداکثر ۳۱ روز آینده قابل مشاهده است")
    return value
