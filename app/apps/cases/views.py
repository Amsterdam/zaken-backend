import logging

from apps.cases import populate
from apps.cases.models import (
    Address,
    Case,
    CaseTimelineReaction,
    CaseTimelineSubject,
    CaseTimelineThread,
    CaseType,
    State,
    StateType,
)
from apps.cases.serializers import (
    AddressSerializer,
    CaseSerializer,
    CaseTimelineReactionSerializer,
    CaseTimelineSerializer,
    CaseTimelineSubjectSerializer,
    CaseTimelineThreadSerializer,
    CaseTypeSerializer,
    FineListSerializer,
    PermitCheckmarkSerializer,
    ResidentsSerializer,
    StateSerializer,
    StateTypeSerializer,
    TimelineAddSerializer,
    TimelineUpdateSerializer,
)
from apps.users.auth_apps import TopKeyAuth
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
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

logger = logging.getLogger(__name__)

bag_id = OpenApiParameter(
    name="bag_id",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description="Verblijfsobjectidentificatie",
)


class GenerateMockViewset(ViewSet):
    def list(self, request):
        populate.delete_all()
        case_types = populate.create_case_types()
        state_types = populate.create_state_types()
        addresses = populate.create_addresses()
        cases = populate.create_cases(case_types, addresses)
        states = populate.create_states(cases, state_types)

        return Response(
            {
                "case_types": CaseTypeSerializer(case_types, many=True).data,
                "addresses": AddressSerializer(addresses, many=True).data,
                "cases": CaseSerializer(cases, many=True).data,
                "state_types": StateTypeSerializer(state_types, many=True).data,
                "states": StateSerializer(states, many=True).data,
            }
        )


class CaseViewSet(ViewSet, ListCreateAPIView, RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    lookup_field = "identification"

    @extend_schema(
        parameters=[bag_id],
        description="Get residents details based on bag id",
        responses={200: ResidentsSerializer()},
    )
    @action(detail=False, methods=["get"], serializer_class=ResidentsSerializer)
    def residents_by_bag_id(self, request):
        bag_id = request.GET.get("bag_id")
        try:
            brp_data = get_brp(bag_id)
            serialized_residents = ResidentsSerializer(data=brp_data)
            serialized_residents.is_valid()

            return Response(serialized_residents.data)

        except Exception as e:
            logger.error(f"Could not retrieve residents for bag id {bag_id}: {e}")

            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], serializer_class=ResidentsSerializer)
    def residents(self, request, identification):
        try:
            case = Case.objects.get(identification=identification)
        except Case.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            bag_id = case.address.bag_id
            brp_data = get_brp(bag_id)
            serialized_residents = ResidentsSerializer(data=brp_data)
            serialized_residents.is_valid()

            return Response(serialized_residents.data)

        except Exception as e:
            logger.error(f"Could not retrieve residents for case {identification}: {e}")

            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
                serialized_state = StateSerializer(state)

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


class AddressViewSet(ViewSet, ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    queryset = Address.objects.all()


class CaseTypeViewSet(ViewSet, ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseTypeSerializer
    queryset = CaseType.objects.all()


class StateTypeViewSet(ViewSet, ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StateTypeSerializer
    queryset = StateType.objects.all()


class StateViewSet(ViewSet, ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StateSerializer
    queryset = State.objects.all()


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

permit_search_parameters = [book_id, query]
permit_request_parameters = [query]


class PermitViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=permit_search_parameters, description="Search query parameters"
    )
    def list(self, request):
        query = request.GET.get("query")
        book_id = request.GET.get("book_id")
        decos_join_response = get_decos_join_permit(query=query, book_id=book_id)
        return Response(decos_join_response)

    @extend_schema(
        parameters=permit_request_parameters, description="Request to Decos Join API"
    )
    @action(detail=False)
    def list_documents(self, request):
        query = request.GET.get("query")

        decos_join_response = get_decos_join_request(query=query)

        return Response(decos_join_response)

    @extend_schema(
        parameters=permit_request_parameters, description="Request to Decos Join API"
    )
    @action(detail=False)
    def list_swagger(self, request):
        query = request.GET.get("query")

        decos_join_response = get_decos_join_request_swagger(query=query)

        return Response(decos_join_response)

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


class CaseTimeLineViewSet(ModelViewSet):
    serializer_class = CaseTimelineSerializer
    queryset = CaseTimelineSubject.objects.all()
    filterset_fields = ["case"]


class CaseTimeLineThreadViewSet(ModelViewSet):
    serializer_class = CaseTimelineThreadSerializer
    queryset = CaseTimelineThread.objects.all()
    permission_classes = [IsAuthenticated | TopKeyAuth]
    filterset_fields = ["subject__case"]

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
            (case, created) = Case.objects.get_or_create(
                identification=serializer.data["case_identification"]
            )
            (
                case_timeline_subject,
                created,
            ) = CaseTimelineSubject.objects.get_or_create(
                case=case, subject=serializer.data["subject"]
            )

            case_timeline_thread = CaseTimelineThread.objects.get(
                id=serializer.data["thread_id"]
            )
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
        parameters=[
            OpenApiParameter(
                name="thread_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="ID of thread",
            )
        ],
        description="Update item from timeline of case (endpoint for automation)",
    )
    @action(
        detail=False, url_name="remove timeline item", url_path="remove-timeline-item"
    )
    def remove_timeline_item(self, request):
        thread_id = request.GET.get("thread_id")

        case_timeline_thread = CaseTimelineThread.objects.get(id=thread_id)
        case_timeline_thread.delete()


class CaseTimeLineReactionViewSet(ModelViewSet):
    serializer_class = CaseTimelineReactionSerializer
    queryset = CaseTimelineReaction.objects.all()
