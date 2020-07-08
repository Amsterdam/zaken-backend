from apps.open_zaak.state_type.serializers import StateTypeSerializer
from apps.open_zaak.state_type.wrappers import StateType
from apps.open_zaak.view_helpers import list_helper, retrieve_helper
from rest_framework import viewsets


class StateTypeViewSet(viewsets.ViewSet):
    serializer_class = StateTypeSerializer
    data_wrapper = StateType
    lookup_field = "uuid"

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)
