from apps.cases import populate
from apps.cases.models import Address, Case, CaseType, State, StateType
from apps.cases.serializers import (
    AddressSerializer,
    CaseSerializer,
    CaseTypeSerializer,
    StateSerializer,
    StateTypeSerializer,
)
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
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
        """ Returns a list of fines for the given case """
        try:
            fines = get_fines(identification)

            # TODO: Remove this once prototyping is done
            if not fines["items"]:
                fines = get_mock_fines(identification)

            return Response(fines)
        except Exception:
            # TODO: Remove this once prototyping is done
            fines = get_mock_fines(identification)
            return Response(fines)

            # TODO: Uncommment this and remove the mock data (when prototyping is done)
            # raise APIException(f"Could not retrieve fine")


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
