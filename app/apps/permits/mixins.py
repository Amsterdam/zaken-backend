import logging

from apps.permits.api_queries_powerbrowser import PowerbrowserRequest
from apps.permits.serializers import PowerbrowserSerializer
from apps.users.permissions import rest_permission_classes_for_ton
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class PermitDetailsMixin:
    @extend_schema(
        description="Get permit details based on bag id",
        responses={200: PowerbrowserSerializer()},
    )
    @action(
        detail=True,
        url_name="permit details",
        url_path="permits",
        permission_classes=rest_permission_classes_for_ton(),
    )
    def permit_details(self, request, bag_id):
        try:
            response = PowerbrowserRequest().get_vergunningen_with_bag_id(bag_id)
            serializer = PowerbrowserSerializer(data=response, many=True)
            if serializer.is_valid():
                deserialized_data = serializer.validated_data
                return Response(deserialized_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"Failed to serialize permits": serializer.errors},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            logger.error(
                f"Failed to fetch permits Powerbrowser for bag id {bag_id}: {e}"
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
