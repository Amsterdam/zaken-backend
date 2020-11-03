import logging

import requests
from apps.cases.filters import CaseFilter
from apps.cases.models import Case, CaseState
from apps.cases.serializers import CaseSerializer
from apps.debriefings.mixins import DebriefingsMixin
from apps.events.mixins import CaseEventsMixin
from apps.fines.mixins import FinesMixin
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

logger = logging.getLogger(__name__)


class TestSerializer(serializers.Serializer):
    request_url = serializers.CharField()


class TestEndPointViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TestSerializer,
        description="request url",
    )
    @action(detail=False, methods=["post"])
    def try_brk_api(self, request):
        serializer = TestSerializer(data=request.data)

        if serializer.is_valid():
            response = requests.get(serializer.data["request_url"])
        return Response(response)


class CaseViewSet(
    ViewSet,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    FinesMixin,
    DebriefingsMixin,
    CaseEventsMixin,
):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    filterset_class = CaseFilter
