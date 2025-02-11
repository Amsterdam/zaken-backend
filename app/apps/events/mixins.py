import logging

from apps.cases.models import Case
from apps.events.serializers import CaseEventSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class CaseEventsMixin:
    @action(detail=True, methods=["get"], serializer_class=CaseEventSerializer)
    def events(self, request, pk):
        try:
            case = Case.objects.get(pk=pk)
        except Case.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            events = case.events.all()
            serialized_events = CaseEventSerializer(data=events, many=True)
            serialized_events.is_valid()

            return Response(serialized_events.data)

        except Exception as e:
            logger.error(f"Could not retrieve events for pk {pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
