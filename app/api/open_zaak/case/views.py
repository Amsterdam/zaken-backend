from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response

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

    def create(self, request):
        data = request.data
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            raise APIException('Serializer error: {}'.format(serializer.errors))

        try:
            # TODO: Process this in the wrapper
            from api.open_zaak.case.services import CaseService
            service = CaseService()

            response = service.post(data.get('zaaktype'),data.get('startdatum'), data.get('omschrijving'))

            object = self.data_wrapper(response)
            serializer = self.serializer_class(object)
            return Response(serializer.data)

        except Exception as e:
            raise APIException('Could not create case: {}'.format(e))