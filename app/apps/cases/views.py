import datetime
import logging
from itertools import cycle

import requests
from apps.cases.filters import CaseFilter
from apps.cases.models import Case, CaseState
from apps.cases.serializers import CaseSerializer
from apps.debriefings.mixins import DebriefingsMixin
from apps.debriefings.models import Debriefing
from apps.fines.mixins import FinesMixin
from apps.users.auth_apps import TopKeyAuth
from apps.visits.models import Visit
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from model_bakery import baker
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
):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    filterset_class = CaseFilter

    @action(detail=False, methods=["get"])
    def mock_cases(self, request):
        start_date = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)

        cases = baker.make(Case, start_date=datetime.date.today(), _quantity=5)

        for case in cases:
            baker.make(
                CaseState, status__name="In looplijst", state_date=start_date, case=case
            )

        baker.make(
            Visit,
            case=cases[1],
            start_time=start_date.replace(hour=10),
            situation=Visit.SITUATION_NOBODY_PRESENT,
            suggest_next_visit="weekend",
            suggest_next_visit_description="Ziet er uit als feesthuis. Grote pakkans in het weekend",
            observations=[
                "malfunctioning_doorbell",
                "vacant",
                "hotel_furnished",
            ],
        )
        baker.make(
            Visit,
            case=cases[2],
            start_time=start_date.replace(hour=10),
            situation=Visit.SITUATION_NOBODY_PRESENT,
            suggest_next_visit="weekend",
            suggest_next_visit_description="Ziet er uit als feesthuis. Grote pakkans in het weekend",
            observations=[
                "malfunctioning_doorbell",
                "vacant",
                "hotel_furnished",
            ],
        )
        baker.make(
            Visit,
            case=cases[2],
            start_time=start_date.replace(hour=14),
            situation=Visit.SITUATION_ACCESS_GRANTED,
            observations=[
                "malfunctioning_doorbell",
                "vacant",
                "hotel_furnished",
            ],
        )
        baker.make(
            Visit,
            case=cases[3],
            start_time=start_date.replace(hour=10),
            situation=Visit.SITUATION_NOBODY_PRESENT,
            suggest_next_visit="weekend",
            suggest_next_visit_description="Ziet er uit als feesthuis. Grote pakkans in het weekend",
            observations=[
                "malfunctioning_doorbell",
                "vacant",
                "hotel_furnished",
            ],
        )
        baker.make(
            Visit,
            case=cases[3],
            start_time=start_date.replace(hour=14),
            situation=Visit.SITUATION_ACCESS_GRANTED,
            observations=[
                "malfunctioning_doorbell",
                "vacant",
                "hotel_furnished",
            ],
        )
        baker.make(
            Visit,
            case=cases[4],
            start_time=start_date.replace(hour=10),
            situation=Visit.SITUATION_NOBODY_PRESENT,
            suggest_next_visit="weekend",
            suggest_next_visit_description="Ziet er uit als feesthuis. Grote pakkans in het weekend",
            observations=[
                "malfunctioning_doorbell",
                "vacant",
                "hotel_furnished",
            ],
        )
        baker.make(
            Visit,
            case=cases[4],
            start_time=start_date.replace(hour=14),
            situation=Visit.SITUATION_ACCESS_GRANTED,
            observations=[
                "malfunctioning_doorbell",
                "vacant",
                "hotel_furnished",
            ],
        )
        baker.make(Debriefing, case=cases[3], violation=Debriefing.VIOLATION_YES)
        baker.make(
            Debriefing,
            case=cases[4],
            violation=Debriefing.VIOLATION_ADDITIONAL_RESEARCH_REQUIRED,
        )

        return Response("OK")
