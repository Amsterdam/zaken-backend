from datetime import datetime

from apps.permits.api_queries_decos_join import DecosJoinRequest
from apps.permits.serializers import DecosSerializer
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

bag_id = OpenApiParameter(
    name="bag_id",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description="Verblijfsobjectidentificatie",
)


class DecosViewSet(ViewSet):
    @extend_schema(
        parameters=[bag_id],
        description="Get decos data based on bag id",
        responses={200: DecosSerializer()},
    )
    @action(detail=False, url_name="details", url_path="details")
    def get_decos_entry_by_bag_id(self, request):
        bag_id = request.GET.get("bag_id")
        dt = datetime.strptime(
            request.GET.get("date", datetime.today().strftime("%Y-%m-%d")), "%Y-%m-%d"
        )

        if not bag_id:
            raise Http404

        response = DecosJoinRequest().get_decos_entry_by_bag_id(bag_id, dt)

        serializer = DecosSerializer(data=response)

        if serializer.is_valid(raise_exception=True):
            return Response(serializer.data)
        return Response(serializer.initial_data)

    @extend_schema(description="test connection with decos")
    @action(detail=False, url_name="test decos connection", url_path="test-connect")
    def get_test_decos_connect(self, request):
        import requests

        response = requests.get(
            "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/"
        )

        if response.ok:
            return Response(response)
        return False
