import logging

import requests
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
)
from apps.cases.serializers import (
    AddressSerializer,
    CaseSerializer,
    CaseTimelineReactionSerializer,
    CaseTimelineSerializer,
    CaseTimelineSubjectSerializer,
    CaseTimelineThreadSerializer,
    FineListSerializer,
    OpenZaakStateSerializer,
    ResidentsSerializer,
    TimelineAddSerializer,
    TimelineUpdateSerializer,
)
from apps.debriefings.serializers import DebriefingSerializer
from apps.permits.mixins import PermitCheckmarkMixin, PermitDetailsMixin
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


class CaseViewSet(ViewSet, ListCreateAPIView, RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    lookup_field = "identification"
    filterset_class = CaseFilter

    @action(detail=True, methods=["get"], serializer_class=CaseTimelineSerializer)
    def timeline(self, request, identification):
        try:
            case = Case.objects.get(identification=identification)
        except Case.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            timeline = case.case_timeline_subjects.all()
            serialized_timeline = CaseTimelineSerializer(data=timeline, many=True)
            serialized_timeline.is_valid()

            return Response(serialized_timeline.data)

        except Exception as e:
            logger.error(f"Could not retrieve timeline for case {identification}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], serializer_class=DebriefingSerializer)
    def debriefings(self, request, identification):
        try:
            case = Case.objects.get(identification=identification)
        except Case.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            debriefings = case.debriefings.all()
            serialized_debriefings = DebriefingSerializer(data=debriefings, many=True)
            serialized_debriefings.is_valid()

            return Response(serialized_debriefings.data)

        except Exception as e:
            logger.error(
                f"Could not retrieve debriefings for case {identification}: {e}"
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # TODO: These are using legacy OpenZaakStateSerializer update later.
    @action(detail=True, methods=["get"], serializer_class=FineListSerializer)
    def fines(self, request, identification):
        """Retrieves states for a case which allow fines, and retrieve the corresponding fines"""
        states = Case.objects.get(identification=identification).states
        eligible_states = states.filter(state_type__invoice_available=True).all()
        states_with_fines = []

        for state in eligible_states:
            try:
                fines = get_fines(state.invoice_identification)
                serialized_fines = FineListSerializer(data=fines)
                serialized_fines.is_valid()
                serialized_state = OpenZaakStateSerializer(state)

                response_dict = {
                    **serialized_state.data,
                    "fines": serialized_fines.data.get("items"),
                }
                states_with_fines.append(response_dict)
            except Exception as e:
                logger.error(
                    f"Could not retrieve fines for {state.invoice_identification}: {e}"
                )

        # TODO: Remove 'items' (because it's mock data) from response once we have an anonimizer
        fines = get_mock_fines("foo_id")
        data = {"items": fines["items"], "states_with_fines": states_with_fines}

        serialized_fines = FineListSerializer(data=data)
        serialized_fines.is_valid()

        return Response(serialized_fines.data)


class AddressViewSet(ViewSet, PermitCheckmarkMixin, PermitDetailsMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    queryset = Address.objects.all()
    lookup_field = "bag_id"

    @action(
        detail=True,
        methods=["get"],
        serializer_class=ResidentsSerializer,
        url_path="residents",
    )
    def residents_by_bag_id(self, request, bag_id):
        try:
            brp_data = get_brp(bag_id)
            serialized_residents = ResidentsSerializer(data=brp_data)
            serialized_residents.is_valid()

            return Response(serialized_residents.data)

        except Exception as e:
            logger.error(f"Could not retrieve residents for bag id {bag_id}: {e}")

            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CaseTimeLineViewSet(ModelViewSet):
    serializer_class = CaseTimelineSerializer
    queryset = CaseTimelineSubject.objects.all()
    filterset_fields = ["case__identification"]


class CaseTimeLineThreadViewSet(ModelViewSet):
    serializer_class = CaseTimelineThreadSerializer
    queryset = CaseTimelineThread.objects.all()
    permission_classes = [IsAuthenticated | TopKeyAuth]
    filterset_fields = ["subject__case__identification"]

    @extend_schema(
        request=TimelineUpdateSerializer,
        description="Add item to timeline of case (endpoint for automation)",
    )
    @action(
        methods=["post"],
        detail=False,
        url_name="add timeline item",
        url_path="add-timeline-item",
    )
    def add_timeline_item(self, request):
        serializer = TimelineAddSerializer(data=request.data)

        if serializer.is_valid():
            (case, created) = Case.objects.get_or_create(
                identification=serializer.data["case_identification"]
            )
            (
                case_timeline_subject,
                created,
            ) = CaseTimelineSubject.objects.get_or_create(
                case=case, subject=serializer.data["subject"]
            )

            case_timeline_thread = CaseTimelineThread()
            # case_timeline_thread.authors = serializer.data["authors"]
            case_timeline_thread.subject = case_timeline_subject
            case_timeline_thread.parameters = serializer.data["parameters"]
            case_timeline_thread.notes = serializer.data["notes"]
            case_timeline_thread.save()

            serializer = CaseTimelineThreadSerializer(case_timeline_thread)

            return Response(serializer.data)
        else:
            logger.error("Update Timeline went wrong")

    @extend_schema(
        request=TimelineUpdateSerializer,
        description="Update item from timeline of case (endpoint for automation)",
    )
    @action(
        methods=["post"],
        detail=False,
        url_name="update timeline item",
        url_path="update-timeline-item",
    )
    def update_timeline_item(self, request):
        serializer = TimelineUpdateSerializer(data=request.data)

        if serializer.is_valid():
            case_timeline_thread = CaseTimelineThread.objects.get(
                id=serializer.data["thread_id"]
            )
            # case_timeline_thread.authors = serializer.data["authors"]
            case_timeline_thread.parameters = serializer.data["parameters"]
            case_timeline_thread.notes = serializer.data["notes"]
            case_timeline_thread.save()

            serializer = CaseTimelineThreadSerializer(case_timeline_thread)

            return Response(serializer.data)
        else:
            logger.error("Update Timeline went wrong")

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="thread_id",
                type=OpenApiTypes.STR,
                required=True,
                description="ID of thread",
            )
        ],
        description="Update item from timeline of case (endpoint for automation)",
    )
    @action(
        detail=False,
        methods=["post"],
        url_name="remove timeline item",
        url_path="remove-timeline-item",
    )
    def remove_timeline_item(self, request):
        thread_id = request.GET.get("thread_id")

        case_timeline_thread = CaseTimelineThread.objects.get(id=thread_id)
        case_timeline_thread.delete()


class CaseTimeLineReactionViewSet(ModelViewSet):
    serializer_class = CaseTimelineReactionSerializer
    queryset = CaseTimelineReaction.objects.all()
