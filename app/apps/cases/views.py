from apps.cases import populate
from apps.cases.models import Address, Case, CaseType, State, StateType
from apps.cases.serializers import (
    AddressSerializer,
    CaseSerializer,
    CaseTypeSerializer,
    FineListSerializer,
    StateSerializer,
    StateTypeSerializer,
)
from rest_framework.decorators import action
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from utils.api_queries_belastingen import get_fines, get_mock_fines


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

    @action(detail=True, methods=["get"])
    def fines(self, request, identification):
        """Retrieves states for a case which allow fines, and retrieve the corresponding fines"""
        states = Case.objects.get(identification=identification).states
        eligible_states = states.filter(state_type__invoice_available=True).all()
        states_with_fines = []

        for state in eligible_states:
            try:
                fines = get_fines(state.invoice_identification)
            except Exception:
                # TODO: Remove this once prototyping is done
                fines = get_mock_fines(state.invoice_identification)
                # TODO: Uncommment this and expand/improve error handling in this function
                # raise APIException(f"Could not retrieve fine")

            serialized_fines = FineListSerializer(data=fines)
            serialized_fines.is_valid()
            serialized_state = StateSerializer(state)

            response_dict = {
                **serialized_state.data,
                "fines": serialized_fines.data.get("items"),
            }
            states_with_fines.append(response_dict)

        # TODO: Remove 'items' from response once the frontend uses 'states_with_fines' instead
        fines = get_mock_fines("foo_id")
        serialized_fines = FineListSerializer(data=fines)
        serialized_fines.is_valid()

        return Response(
            {**serialized_fines.data, "states_with_fines": states_with_fines}
        )


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
