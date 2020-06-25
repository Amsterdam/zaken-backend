# TODO: This just default to the first case type, something smarter should be done here
# TODO: Hier moet er een get_or_create komen

from datetime import date
from django.http import HttpResponseBadRequest
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from api.gateway.push.serializers import PushSerializer
from api.open_zaak.case_type.services import CaseTypeService
from api.open_zaak.case.services import CaseService
from api.open_zaak.case_object.services import CaseObjectService

class PushViewSet(viewsets.ViewSet):
    serializer_class = PushSerializer

    def create(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            raise APIException('Serializer error: {}'.format(serializer.errors))

        case_id = data.get('case_id')
        
        try:

            case_type_service = CaseTypeService()
            case_type = case_type_service.get()['results'][0]['url']
            case_service = CaseService()

            case = case_service.post(
                data={
                    "identificatie": case_id,
                    "omschrijving": "Hello World",
                    "startdatum": str(date.today()),
                    "einddatum": str(date.today()),
                    "zaaktype": case_type,
                }
            )

        except Exception as e:
            return Response(
                {'message': 'Could not create object', 'error': str(e)},
                status=HttpResponseBadRequest.status_code
            )

        return Response(case)