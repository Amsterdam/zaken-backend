from apps.cases import populate
from apps.cases.models import Address, Case, CaseType
from apps.cases.serializers import AddressSerializer, CaseSerializer, CaseTypeSerializer
from django.http import JsonResponse
from django.shortcuts import render
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


class CaseViewSet(ViewSet, ListCreateAPIView, RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()

    def update(self, request, partial, pk, **kwargs):
        # TODO: Update here
        return JsonResponse({"message": "Hello World"})
        # model_object = self.get_object(pk)

    def patch(self, request, pk):
        return JsonResponse({"message": "Hello World PATCH"})
        # model_object = self.get_object(pk)
        # serializer = self.serializer_class(
        #     model_object, data=request.data, partial=True
        # )
        # if serializer.is_valid():
        #     serializer.save()
        #     return JsonResponse(code=201, data=serializer.data)
        # return JsonResponse(code=400, data="wrong parameters")


class AddressViewSet(ViewSet, ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    queryset = Address.objects.all()


class CaseTypeViewSet(ViewSet, ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseTypeSerializer
    queryset = CaseType.objects.all()
