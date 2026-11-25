from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.models import Appointment
from appointments.serializers.appointment import AppointmentSerializer
from appointments.services.cancel_booking import (
    CancelValidationError,
    cancel_appointment,
)


class CancelBookingView(APIView):
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
        try:
            result = cancel_appointment(appointment, by_user=request.user)
        except CancelValidationError as e:
            return Response(
                {"detail": str(e), "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = AppointmentSerializer(result["appointment"]).data
        data["refund_rate"] = str(result["refund_rate"])
        data["refund_amount"] = str(result["refund_amount"])
        return Response(data, status=status.HTTP_200_OK)