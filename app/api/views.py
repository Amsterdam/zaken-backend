from django.http import HttpResponseBadRequest
from rest_framework import viewsets
from rest_framework.response import Response

from api.serializers import StateTypeSerializer
from wrappers.state_type import StateType

class StateTypeViewSet(viewsets.ViewSet):
    queryset = None
    serializer_class = StateTypeSerializer

    def retrieve(self, request, pk):
        try:
            state_type = StateType.retrieve(pk)
            serializer = StateTypeSerializer(state_type)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'message': 'Could not retrieve object', 'error': str(e) },
                status=HttpResponseBadRequest.status_code
            )

    def list(self, request):
        state_types = StateType.retrieve_all()
        serializer = StateTypeSerializer(state_types, many=True)
        return Response(serializer.data)