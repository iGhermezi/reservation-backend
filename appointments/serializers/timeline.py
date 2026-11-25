from rest_framework import serializers

from appointments.models import AppointmentLog


class AppointmentLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AppointmentLog
        fields = ["action", "note", "actor_name", "created_at"]

    def get_actor_name(self, obj):
        if obj.actor is None:
            return None
        return obj.actor.get_full_name()
