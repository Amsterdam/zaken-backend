from rest_framework import viewsets

from api.open_zaak.state_type.serializers import StateTypeSerializer
from api.open_zaak.state_type.wrappers import StateType
from api.views import retrieve_helper, list_helper


class StateTypeViewSet(viewsets.ViewSet):
    serializer_class = StateTypeSerializer
    data_wrapper = StateType
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)
