from apps.permits.api_queries_decos_join import DecosJoinRequest
from apps.permits.serializers import DecosPermitSerializer, PermitCheckmarkSerializer
from django.shortcuts import render
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class PermitCheckmarkMixin:
    @extend_schema(
        description="Get permit checkmarks based on bag id",
        responses={200: PermitCheckmarkSerializer()},
    )
    @action(detail=True, url_name="permit checkmarks", url_path="permits/checkmarks")
    def checkmarks(self, request, bag_id):
        response = DecosJoinRequest().get_checkmarks_by_bag_id(bag_id)

        serializer = PermitCheckmarkSerializer(data=response)

        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.initial_data)


class PermitDetailsMixin:
    @extend_schema(
        description="Get permit details based on bag id",
        responses={200: DecosPermitSerializer(many=True)},
    )
    @action(detail=True, url_name="permit details", url_path="permits")
    def permit_details(self, request, bag_id):
        response = DecosJoinRequest().get_permits_by_bag_id(bag_id)
        serializer = DecosPermitSerializer(data=response, many=True)

        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.initial_data)
