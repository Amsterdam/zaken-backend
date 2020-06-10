from django.http import HttpResponseBadRequest
from rest_framework import viewsets
from rest_framework.response import Response

from api.serializers import StateTypeSerializer, CaseObjectSerializer, CaseTypeSerializer, CaseSerializer, CatalogSerializer, StateSerializer
from wrappers.state_type import StateType
from wrappers.case_object import CaseObject
from wrappers.case_type import CaseType
from wrappers.case import Case
from wrappers.catalog import Catalog
from wrappers.state import State

class StateTypeViewSet(viewsets.ViewSet):
    serializer_class = StateTypeSerializer
    data_wrapper = StateType
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)

class CaseObjectViewSet(viewsets.ViewSet):
    serializer_class = CaseObjectSerializer
    data_wrapper = CaseObject
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)

class CaseTypeViewSet(viewsets.ViewSet):
    serializer_class = CaseTypeSerializer
    data_wrapper = CaseType
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)

class CaseViewSet(viewsets.ViewSet):
    serializer_class = CaseSerializer
    data_wrapper = Case
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)

class CatalogViewSet(viewsets.ViewSet):
    serializer_class = CatalogSerializer
    data_wrapper = Catalog
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)


class StateViewSet(viewsets.ViewSet):
    serializer_class = StateSerializer
    data_wrapper = State
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)

# Todo: cleanup helpers later
def retrieve_helper(self, uuid):
    try:
        object = self.data_wrapper.retrieve(uuid)
        serializer = self.serializer_class(object)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'message': 'Could not retrieve object', 'error': str(e)},
            status=HttpResponseBadRequest.status_code
        )

def list_helper(self):
    objects = self.data_wrapper.retrieve_all()
    serializer = self.serializer_class(objects, many=True)
    return Response(serializer.data)

def list_debug(self):
    objects = self.data_wrapper.retrieve_all()
    return Response({'objects': objects})