from rest_framework import serializers


class RescheduleSerializer(serializers.Serializer):
    start_at = serializers.DateTimeField()
