from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.models import Appointment
from appointments.serializers.timeline import AppointmentLogSerializer


class AppointmentTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        try:
            appointment = Appointment.objects.get(
                public_id=public_id,
                customer=request.user,
            )
        except Appointment.DoesNotExist:
            return Response(
                {"detail": "نوبت پیدا نشد", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        logs = appointment.logs.select_related("actor").order_by("created_at")
        return Response(AppointmentLogSerializer(logs, many=True).data)
