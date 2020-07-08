from apps.open_zaak.case_object.serializers import CaseObjectSerializer
from apps.open_zaak.case_object.wrappers import CaseObject
from apps.open_zaak.view_helpers import create_helper, list_helper, retrieve_helper
from rest_framework import viewsets


class CaseObjectViewSet(viewsets.ViewSet):
    serializer_class = CaseObjectSerializer
    data_wrapper = CaseObject
    lookup_field = "uuid"

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)

    def create(self, request):
        return create_helper(self, request.data)
