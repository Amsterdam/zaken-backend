from apps.cases import populate
from apps.cases.models import Address, Case, CaseType
from apps.cases.serializers import AddressSerializer, CaseSerializer, CaseTypeSerializer
from django.shortcuts import render
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class GenerateMockViewset(ViewSet):
    def list(self, request):
        populate.delete_all()
        case_types = populate.create_case_types()
        addresses = populate.create_addresses()
        cases = populate.create_cases(case_types, addresses)

        return Response(
            {
                "case_types": CaseTypeSerializer(case_types, many=True).data,
                "addresses": AddressSerializer(addresses, many=True).data,
                "cases": CaseSerializer(cases, many=True).data,
            }
        )


class CaseViewSet(ViewSet, ListCreateAPIView, RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()


class AddressViewSet(ViewSet, ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    queryset = Address.objects.all()


class CaseTypeViewSet(ViewSet, ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseTypeSerializer
    queryset = CaseType.objects.all()
