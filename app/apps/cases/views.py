import datetime
import logging
from itertools import cycle

import requests
from apps.addresses.models import Address
from apps.cases.filters import CaseFilter
from apps.cases.models import Case, CaseState
from apps.cases.serializers import CaseSerializer
from apps.debriefings.mixins import DebriefingsMixin
from apps.debriefings.models import Debriefing
from apps.events.mixins import CaseEventsMixin
from apps.fines.mixins import FinesMixin
from apps.users.auth_apps import TopKeyAuth
from apps.users.models import User
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
    CaseEventsMixin,
):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    filterset_class = CaseFilter

    @action(detail=False, methods=["get"])
    def mock_cases(self, request):
        start_date = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        address = baker.make(
            Address,
            street_name="Amstel",
            number="1",
            postal_code="1011 PN",
            bag_id="0363200012145295",
        )

        cases = baker.make(
            Case, start_date=datetime.date.today(), address=address, _quantity=5
        )
        user_1, _ = User.objects.get_or_create(
            email="jake.gyllenhaal@example.com",
            first_name="Jake",
            last_name="Gyllenhaal",
        )
        user_2, _ = User.objects.get_or_create(
            email="jessica.chastain@example.com",
            first_name="Jessica",
            last_name="Chastain",
        )

        authors = User.objects.filter(id__in=[user_1.id, user_2.id])

        for case in cases:
            baker.make(
                CaseState, status__name="In looplijst", state_date=start_date, case=case
            )

        for case in [cases[1], cases[2], cases[3], cases[4]]:
            baker.make(
                Visit,
                case=case,
                start_time=start_date.replace(hour=10),
                situation=Visit.SITUATION_NOBODY_PRESENT,
                suggest_next_visit="weekend",
                suggest_next_visit_description="Ziet er uit als feesthuis. Grote pakkans in het weekend",
                observations=[
                    "malfunctioning_doorbell",
                    "vacant",
                    "hotel_furnished",
                ],
                authors=authors,
            )

        for case in [cases[2], cases[3], cases[4]]:
            baker.make(
                Visit,
                case=case,
                start_time=start_date.replace(hour=14),
                situation=Visit.SITUATION_ACCESS_GRANTED,
                observations=[
                    "malfunctioning_doorbell",
                    "vacant",
                    "hotel_furnished",
                ],
                authors=authors,
            )

        baker.make(Debriefing, case=cases[3], violation=Debriefing.VIOLATION_YES)
        baker.make(
            Debriefing,
            case=cases[4],
            violation=Debriefing.VIOLATION_ADDITIONAL_RESEARCH_REQUIRED,
        )

        return Response("OK")
