from services.service import create_service
from services.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_STATES

service = create_service(OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_STATES)

def add_state_to_case(case_url, state_type_url):
    data = {
        'zaak': case_url,
        'statustype': state_type_url,
        'datumStatusGezet': '2020-05-28 12:30',
        'statustoelichting': 'Leuke notitie hierzo' # doesn't seem to be processed/saved
    }

    return service.post(SUB_DOMAIN_STATES, data)
