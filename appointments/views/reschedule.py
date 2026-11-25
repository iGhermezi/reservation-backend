from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.models import Appointment
from appointments.serializers.appointment import AppointmentSerializer
from appointments.serializers.reschedule import RescheduleSerializer
from appointments.services.create_booking import SlotTakenError
from appointments.services.reschedule_booking import (
    RescheduleValidationError,
    reschedule_appointment,
)


class RescheduleBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        try:
            appointment = Appointment.objects.get(public_id=public_id)
        except Appointment.DoesNotExist:
            return Response(
                {"detail": "نوبت پیدا نشد", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if appointment.customer_id != request.user.id:
            return Response(
                {"detail": "نوبت پیدا نشد", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = RescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = reschedule_appointment(
                appointment,
                by_user=request.user,
                new_start_at=serializer.validated_data["start_at"],
            )
        except SlotTakenError as e:
            return Response(
                {"detail": str(e), "code": "slot_taken"},
                status=status.HTTP_409_CONFLICT,
            )
        except RescheduleValidationError as e:
            return Response(
                {"detail": str(e), "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            AppointmentSerializer(updated).data, status=status.HTTP_200_OK
        )