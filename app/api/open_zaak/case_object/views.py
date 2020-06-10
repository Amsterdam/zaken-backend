from rest_framework import viewsets
from api.open_zaak.case_object.serializers import CaseObjectSerializer
from api.open_zaak.case_object.wrappers import CaseObject
from api.views import retrieve_helper, list_helper

class CaseObjectViewSet(viewsets.ViewSet):
    serializer_class = CaseObjectSerializer
    data_wrapper = CaseObject
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)


# from services.service import create_service
# from services.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_CASE_OBJECTS
#
# service = create_service(OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_CASE_OBJECTS)
#
#
# def add_bag_object_to_case(case_url, bag_url):
#     add_object_to_case(case_url, bag_url, 'adres')
#
#
# def add_object_to_case(case_url, object_url, object_type):
#     data = {
#         'zaak': case_url,
#         'object': object_url,
#         'object_type': object_type,
#     }
#
#     return service.post(SUB_DOMAIN_CASE_OBJECTS, data)
#
#
# def get_case_objects():
#     return service.get(SUB_DOMAIN_CASE_OBJECTS)