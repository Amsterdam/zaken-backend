from datetime import datetime

from apps.permits.api_queries_decos_join import DecosJoinRequest
from apps.permits.serializers import DecosPermitSerializer
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response


class PermitDetailsMixin:
    @extend_schema(
        description="Get permit details based on bag id",
        responses={200: DecosPermitSerializer(many=True)},
    )
    @action(detail=True, url_name="permit details", url_path="permits")
    def permit_details(self, request, bag_id, dt=None):
        if not dt:
            dt = datetime.today()
        response = DecosJoinRequest().get_decos_entry_by_bag_id(bag_id, dt)
        serializer = DecosPermitSerializer(data=response, many=True)

        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.initial_data)
