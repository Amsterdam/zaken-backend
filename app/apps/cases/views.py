from apps.cases import populate
from apps.cases.models import Case
from apps.cases.serializers import AddressSerializer, CaseSerializer, ProjectSerializer
from django.shortcuts import render
from rest_framework.generics import GenericAPIView
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


class CaseViewSet(ViewSet, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
