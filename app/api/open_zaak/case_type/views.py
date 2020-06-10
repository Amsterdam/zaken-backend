from rest_framework  import viewsets
from api.open_zaak.case_type.serializers import CaseTypeSerializer
from api.open_zaak.case_type.wrappers import CaseType
from api.views import retrieve_helper, list_helper

class CaseTypeViewSet(viewsets.ViewSet):
    serializer_class = CaseTypeSerializer
    data_wrapper = CaseType
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)