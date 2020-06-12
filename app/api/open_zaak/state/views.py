from rest_framework import viewsets
from api.open_zaak.state.serializer import StateSerializer
from api.open_zaak.state.wrappers import State
from api.views import retrieve_helper, list_helper, create_helper

class StateViewSet(viewsets.ViewSet):
    serializer_class = StateSerializer
    data_wrapper = State
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)

    def create(self, request):
        return create_helper(self, request.data)
