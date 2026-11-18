from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.serializers.appointment import AppointmentSerializer
from appointments.serializers.create_booking import CreateBookingSerializer
from appointments.services.create_booking import SlotTakenError, create_booking


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
            )
        except SlotTakenError as e:
            return Response(
                {"detail": str(e), "code": "slot_taken"},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            AppointmentSerializer(appt).data,
            status=status.HTTP_201_CREATED,
        )
