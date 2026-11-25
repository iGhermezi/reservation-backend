from rest_framework import serializers

from appointments.models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "public_id",
            "business",
            "customer",
            "provider",
            "service",
            "start_at",
            "end_at",
            "duration_minutes",
            "price_final",
            "deposit_amount",
            "status",
            "occupies_until",
            "review_deadline_at",
            "status_reason",
            "created_via",
            "custom_values",
        ]
        read_only_fields = [
            "public_id",
            "end_at",
            "duration_minutes",
            "price_final",
            "deposit_amount",
            "status",
            "occupies_until",
            "review_deadline_at",
            "created_via",
        ]
