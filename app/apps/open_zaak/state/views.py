from apps.open_zaak.state.serializer import LegacyStateSerializer
from apps.open_zaak.state.wrappers import LegacyState
from apps.open_zaak.view_helpers import create_helper, list_helper, retrieve_helper
from rest_framework import viewsets


class LegacyStateViewSet(viewsets.ViewSet):
    serializer_class = LegacyStateSerializer
    data_wrapper = LegacyState
    lookup_field = "uuid"

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)

    def create(self, request):
        return create_helper(self, request.data)
