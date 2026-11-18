from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Provider, Service
from scheduling.serializers.free_slots import FreeSlotsQuerySerializer
from scheduling.services.free_slots import get_free_slots


class FreeSlotsView(APIView):
    def get(self, request):
        serializer = FreeSlotsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        provider = Provider.objects.get(id=serializer.validated_data["provider"])
        service = Service.objects.get(id=serializer.validated_data["service"])
        slots = get_free_slots(
            provider, service, serializer.validated_data["date"]
        )
        return Response({"slots": [s.strftime("%H:%M") for s in slots]})
