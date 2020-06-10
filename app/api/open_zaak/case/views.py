from rest_framework import viewsets
from api.open_zaak.case.serializers import CaseSerializer
from api.open_zaak.case.wrappers import Case
from api.views import retrieve_helper, list_helper

class CaseViewSet(viewsets.ViewSet):
    serializer_class = CaseSerializer
    data_wrapper = Case
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)