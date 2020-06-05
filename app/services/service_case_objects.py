from app.services.service import create_service
from app.services.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_CASE_OBJECTS

service = create_service(OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_CASE_OBJECTS)


def add_bag_object_to_case(case_url, bag_url):
    add_object_to_case(case_url, bag_url, 'adres')


def add_object_to_case(case_url, object_url, object_type):
    data = {
        'zaak': case_url,
        'object': object_url,
        'object_type': object_type,
    }

    return service.post(SUB_DOMAIN_CASE_OBJECTS, data)


def get_case_objects():
    return service.get(SUB_DOMAIN_CASE_OBJECTS)
