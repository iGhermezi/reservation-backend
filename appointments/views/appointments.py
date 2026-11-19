from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.serializers.appointment import AppointmentSerializer
from appointments.serializers.create_booking import CreateBookingSerializer
from appointments.services.create_booking import (
    BookingValidationError,
    SlotTakenError,
    create_booking,
)


class CreateBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            appt = create_booking(
                customer=request.user,
                provider_id=serializer.validated_data["provider"],
                service=serializer.validated_data["service_obj"],
                start_at=serializer.validated_data["start_at"],
                duration_minutes=serializer.validated_data.get("duration_minutes"),
            )
        except SlotTakenError as e:
            return Response(
                {"detail": str(e), "code": "slot_taken"},
                status=status.HTTP_409_CONFLICT,
            )
        except BookingValidationError as e:
            return Response(
                {"detail": str(e), "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            AppointmentSerializer(appt).data,
            status=status.HTTP_201_CREATED,
        )
