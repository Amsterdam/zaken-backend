# TODO: This just default to the first case type, something smarter should be done here

from datetime import date
from django.http import HttpResponseBadRequest
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from api.gateway.push.serializers import PushSerializer
from api.open_zaak.case_type.services import CaseTypeService
from api.open_zaak.case.services import CaseService

class PushViewSet(viewsets.ViewSet):
    serializer_class = PushSerializer

    def create(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            raise APIException('Serializer error: {}'.format(serializer.errors))

        try:
            case_id = data.get('case_id')
            case = self.get_case(case_id)

            if not case:
                case = self.create_case(data)

            return Response(case)

        except Exception as e:
            return Response(
                {'message': 'Could not create case', 'error': str(e)},
                status=HttpResponseBadRequest.status_code
            )

    def get_case(self, case_id):
        case_service = CaseService()
        response = case_service.get(params={'identificatie': case_id})

        if response.get('count') > 0:
            case = response.get('results')[0]
            return case

    def create_case(self, data):
        case_type_service = CaseTypeService()
        case_type = case_type_service.get()['results'][0]['url']

        case_service = CaseService()
        case_id = data.get('case_id')
        case = case_service.post(
            data={
                "identificatie": case_id,
                "omschrijving": "Hello World",
                "startdatum": str(date.today()),
                "einddatum": str(date.today()),
                "zaaktype": case_type,
            }
        )

        return case