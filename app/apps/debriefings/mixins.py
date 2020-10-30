import logging

from apps.cases.models import Case
from apps.debriefings.serializers import DebriefingSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class DebriefingsMixin:
    @action(detail=True, methods=["get"], serializer_class=DebriefingSerializer)
    def debriefings(self, request, pk):
        try:
            case = Case.objects.get(pk=pk)
        except Case.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            debriefings = case.debriefings.all()
            serialized_debriefings = DebriefingSerializer(data=debriefings, many=True)
            serialized_debriefings.is_valid()

            return Response(serialized_debriefings.data)

        except Exception as e:
            logger.error(f"Could not retrieve debriefings for pk {pk}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
