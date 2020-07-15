from apps.cases import populate
from apps.cases.models import Address, Case, Project
from apps.cases.serializers import AddressSerializer, CaseSerializer, ProjectSerializer
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
        projects = populate.create_projects()
        addresses = populate.create_addresses()
        cases = populate.create_cases(projects, addresses)

        return Response(
            {
                "projects": ProjectSerializer(projects, many=True).data,
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


class ProjectViewSet(ViewSet, ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
