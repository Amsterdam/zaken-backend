from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.open_zaak.case.services import CaseService
from api.open_zaak.case_object.services import CaseObjectService
from api.open_zaak.case_type.services import CaseTypeService
from api.open_zaak.catalog.services import CatalogService
from api.open_zaak.state.services import StateService
from api.open_zaak.state_type.services import StateTypeService
from api.open_zaak.information_object_type.services import InformationObjectTypeService


class GenerateMockViewset(viewsets.ViewSet):
    @action(detail=False, methods=['delete'])
    def delete(self, request=None):
        responses = []

        information_object_type_service = InformationObjectTypeService()
        information_object_types = information_object_type_service.get()

        for information_object_type in information_object_types['results']:
          information_object_type_id = information_object_type['url'].split('/')[-1]
          response = information_object_type_service.delete(information_object_type_id)
          responses.append(response)

        case_type_service = CaseTypeService()
        case_types = case_type_service.get()['results']
        
        for case_type in case_types:
            case_type_id = case_type['url'].split('/')[-1]
            response = case_type_service.delete(case_type_id)
            responses.append(response)

        return Response({
            'responses': responses
        })

    def list(self, request):
        # First delete al data
        self.delete()
       
        # Create Catalog
        catalog_service = CatalogService()
        catalog = catalog_service.mock()
        catalog_url = catalog['url']

        # Create Information Object Type
        information_object_type_service = InformationObjectTypeService()
        information_object_type = information_object_type_service.mock(catalog_url)
        information_object_type_url = information_object_type['url']
        information_object_type_id = information_object_type_url.split('/')[-1]
        information_object_type = information_object_type_service.publish(information_object_type_id)

        # Create Case Type
        case_type_service = CaseTypeService()
        case_type = case_type_service.mock(catalog_url)
        case_type_url = case_type['url']
        case_type_id = case_type_url.split('/')[-1]

        # Create StateTypes
        state_type_service = StateTypeService()
        state_types = state_type_service.mock(case_type_url)

        # Publish case type
        case_type_service.publish(case_type_id)

        # Add Cases
        case_service = CaseService()
        cases = case_service.mock(case_type_url)

        # Add a state and case objects to all cases
        states = []
        case_objects = []

        for case in cases:
            case_url = case['url']
        
            # state_services = StateService()
            # response = state_services.mock(state_types, case_url)
            # states.append(response)
        
            case_object_service = CaseObjectService()
            response = case_object_service.mock(case_url)
            case_objects.append(response)

        return Response({
            'catalog': catalog,
            'information_object_type': information_object_type,
            'case_type': case_type,
            'state_types': state_types,
            'cases': cases,
            # 'states': states,
            'case_objects': case_objects
        })
