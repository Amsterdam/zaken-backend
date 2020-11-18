import logging

from apps.cases.models import Case
from apps.fines.api_queries_belastingen import get_fines, get_mock_fines
from apps.fines.serializers import FineListSerializer
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class FinesMixin:
    @action(detail=True, methods=["get"], serializer_class=FineListSerializer)
    def fines(self, request, pk):
        """Retrieves states for a case which allow fines, and retrieve the corresponding fines"""
        try:
            case = Case.objects.get(pk=pk)
        except Case.DoesNotExist:
            raise NotFound("Case does not exist")

        fines = case.fines.all()
        items = []
        for fine in fines:
            try:
                fines = get_fines(fine.identification)
                serialized_fines = FineListSerializer(data=fines)
                serialized_fines.is_valid()

                response_dict = {
                    "fines": serialized_fines.data.get("items"),
                }
                items.append(response_dict)
            except Exception as e:
                logger.error(f"Could not retrieve fines for {fine.identification}: {e}")

        mock_items = get_mock_fines("foo_id")["items"]
        data = {"mock_items": mock_items, "items": items}

        serialized_fines = FineListSerializer(data=data)
        serialized_fines.is_valid()

        return Response(serialized_fines.data)
