from services.service import Service
from services.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_CASE_OBJECTS, SUB_DOMAINS_CASES

class CaseObjectsService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CASES
    TYPES = SUB_DOMAINS_CASES
    DATA_TYPE = SUB_DOMAIN_CASE_OBJECTS

    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response


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
