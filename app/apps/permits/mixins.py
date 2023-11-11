import logging
from datetime import datetime

from apps.permits.api_queries_decos_join import DecosJoinRequest
from apps.permits.api_queries_powerbrowser import PowerbrowserRequest
from apps.permits.serializers import DecosSerializer, PowerbrowserSerializer
from apps.users.permissions import rest_permission_classes_for_ton
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class PermitDetailsMixin:
    @extend_schema(
        description="Get Decos permit details based on bag id",
        responses={200: DecosSerializer()},
    )
    @action(
        detail=True,
        url_name="permit details",
        url_path="permits",
        permission_classes=rest_permission_classes_for_ton(),
    )
    def permit_details(self, request, bag_id, dt=None):
        if not dt:
            dt = datetime.today()
        response = DecosJoinRequest().get_decos_entry_by_bag_id(bag_id, dt)
        serializer = DecosSerializer(data=response)

        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.initial_data)

    @extend_schema(
        description="Get PowerBrowser permit details based on bag id",
        responses={200: PowerbrowserSerializer()},
    )
    @action(
        detail=True,
        url_name="permit details PowerBrowser",
        url_path="permitsbb",
        permission_classes=rest_permission_classes_for_ton(),
    )
    def get_bb_permit_details(self, request, bag_id):
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
