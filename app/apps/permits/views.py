from apps.permits.api_queries_decos_join import DecosJoinRequest
from apps.permits.serializers import DecosPermitSerializer, PermitCheckmarkSerializer
from django.shortcuts import render
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

query = OpenApiParameter(
    name="query",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description="Query",
)

book_id = OpenApiParameter(
    name="book_id",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description=(
        "BAG Objecten: 90642DCCC2DB46469657C3D0DF0B1ED7 or Objecten onbekend:"
        " B1FF791EA9FA44698D5ABBB1963B94EC"
    ),
)

object_id = OpenApiParameter(
    name="object_id",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description="ID van woningobject",
)

bag_id = OpenApiParameter(
    name="bag_id",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description="Verblijfsobjectidentificatie",
)


permit_search_parameters = [book_id, query]
permit_request_parameters = [query]


class PermitViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[bag_id],
        description="Get permit checkmarks based on bag id",
        responses={200: PermitCheckmarkSerializer()},
    )
    @action(detail=False, url_name="permit checkmarks", url_path="checkmarks")
    def get_permit_checkmarks(self, request):
        bag_id = request.GET.get("bag_id")
        response = DecosJoinRequest().get_checkmarks_by_bag_id(bag_id)

        serializer = PermitCheckmarkSerializer(data=response)

        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.initial_data)

    @extend_schema(
        parameters=[bag_id],
        description="Get permit details based on bag id",
        responses={200: DecosPermitSerializer(many=True)},
    )
    @action(detail=False, url_name="permit details", url_path="details")
    def get_permit_details(self, request):
        bag_id = request.GET.get("bag_id")
        response = DecosJoinRequest().get_permits_by_bag_id(bag_id)

        serializer = DecosPermitSerializer(data=response, many=True)

        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.initial_data)
