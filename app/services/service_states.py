from services.service import create_service
from services.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_STATES

service = create_service(OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_STATES)

def add_state_to_case(case_uri, state_type_uri):
    data = {
        'zaak': case_uri,
        'statustype': state_type_uri,
        'datumStatusGezet': '2020-05-28 12:30'
    }

    return service.post(SUB_DOMAIN_STATES, data)
