# TODO: This just default to the first case type, something smarter should be done here
from django.http import HttpResponseBadRequest
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from api.gateway.push.serializers import PushSerializer, PushCheckActionSerializer
from api.open_zaak.case_type.services import CaseTypeService
from api.open_zaak.case.services import CaseService

class PushCheckActionViewSet(viewsets.ViewSet):
    # View for registering Check action (from the Top application mainly)
    # Note: This is subject to change. Check is too specific, and we'll probably add some more data regarding a visit here.
    serializer_class = PushCheckActionSerializer

    def create(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            raise APIException(f'Serializer error: {serializer.errors}')

        try:
            identificatie = data.get('identificatie')
            case = get_case(identificatie)
        except Exception as e:
            raise APIException(f'Could not get case: {e}')

        try:
            checked_action = data.get("check_actie")
            print(f'Creating checked {checked_action} action object with case {case}')
            return Response(case)
        except Exception as e:
            raise APIException(f'Could not create checked action: {e}')


class PushViewSet(viewsets.ViewSet):
    serializer_class = PushSerializer

    def create(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            raise APIException(f'Serializer error: {serializer.errors}')

        try:
            identificatie = data.get('identificatie')
            case = get_case(identificatie)

            if not case:
                case = create_case(data)

            return Response(case)

        except Exception as e:
            raise APIException(f'Could not get or create case: {e}')

def get_case(identificatie):
    case_service = CaseService()
    response = case_service.get(params={'identificatie': identificatie})

    if response.get('count') > 0:
        case = response.get('results')[0]
        return case

def create_case(data):
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