import logging

from apps.cases.models import Case
from apps.fines.api_queries_belastingen import get_fines, get_mock_fines
from apps.fines.serializers import FineListSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class FinesMixin:
    @action(detail=True, methods=["get"], serializer_class=FineListSerializer)
    def fines(self, request, identification):
        """Retrieves states for a case which allow fines, and retrieve the corresponding fines"""

        fines = Case.objects.get(identification=identification).fines.all()
        for fine in fines:
            try:
                fines = get_fines(fine.identification)
                serialized_fines = FineListSerializer(data=fines)
                serialized_fines.is_valid()

                response_dict = {
                    "fines": serialized_fines.data.get("items"),
                }
                fines.append(response_dict)
            except Exception as e:
                logger.error(f"Could not retrieve fines for {fine.identification}: {e}")

        # TODO: Remove 'items' (because it's mock data) from response once we have an anonimizer
        fines = get_mock_fines("foo_id")
        data = {"items": fines["items"], "states_with_fines": fines}

        serialized_fines = FineListSerializer(data=data)
        serialized_fines.is_valid()

        return Response(serialized_fines.data)
