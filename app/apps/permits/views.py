import logging

import requests
from apps.cases import populate
from apps.cases.filters import CaseFilter
from apps.cases.models import (
    Address,
    Case,
    CaseState,
    CaseStateType,
    CaseTimelineReaction,
    CaseTimelineSubject,
    CaseTimelineThread,
    CaseType,
    OpenZaakState,
    OpenZaakStateType,
)
from apps.cases.serializers import (
    AddressSerializer,
    CaseSerializer,
    CaseStateSerializer,
    CaseStateTypeSerializer,
    CaseTimelineReactionSerializer,
    CaseTimelineSerializer,
    CaseTimelineSubjectSerializer,
    CaseTimelineThreadSerializer,
    CaseTypeSerializer,
    FineListSerializer,
    OpenZaakStateSerializer,
    OpenZaakStateTypeSerializer,
    PermitCheckmarkSerializer,
    ResidentsSerializer,
    TimelineAddSerializer,
    TimelineUpdateSerializer,
)
from apps.debriefings.serializers import DebriefingSerializer
from apps.users.auth_apps import TopKeyAuth
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from utils.api_queries_belastingen import get_fines, get_mock_fines
from utils.api_queries_brp import get_brp
from utils.api_queries_decos_join import (
    DecosJoinRequest,
    get_decos_join_permit,
    get_decos_join_request,
    get_decos_join_request_swagger,
)
from utils.serializers import DecosPermitSerializer

bag_id = OpenApiParameter(
    name="bag_id",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description="Verblijfsobjectidentificatie",
)


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
