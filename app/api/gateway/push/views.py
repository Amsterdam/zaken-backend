# TODO: This just default to the first case type, something smarter should be done here
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
            identificatie = data.get('identificatie')
            case = self.get_case(identificatie)

            if not case:
                case = self.create_case(data)

            return Response(case)

        except Exception as e:
            return Response(
                {'message': 'Could not create case', 'error': str(e)},
                status=HttpResponseBadRequest.status_code
            )

    def get_case(self, identificatie):
        case_service = CaseService()
        response = case_service.get(params={'identificatie': identificatie})

        if response.get('count') > 0:
            case = response.get('results')[0]
            return case

    def create_case(self, data):
        case_type_service = CaseTypeService()
        case_type = case_type_service.get()['results'][0]['url']
        case_service = CaseService()
        case = case_service.post(
            data={
                "identificatie": data['identificatie'],
                "omschrijving": data['omschrijving'],
                "toelichting": data['toelichting'],
                "startdatum": data['startdatum'],
                "einddatum": data.get('einddatum'),
                "zaaktype": case_type,
            }
        )

        return case