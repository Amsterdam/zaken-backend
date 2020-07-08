from apps.open_zaak.case_type.serializers import CaseTypeSerializer
from apps.open_zaak.case_type.wrappers import CaseType
from apps.open_zaak.view_helpers import list_helper, retrieve_helper
from rest_framework import viewsets


class CaseTypeViewSet(viewsets.ViewSet):
    serializer_class = CaseTypeSerializer
    data_wrapper = CaseType
    lookup_field = "uuid"

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)
