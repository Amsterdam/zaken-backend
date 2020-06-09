from services.service import create_service
from services.settings import OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS, SUB_DOMAIN_STATE_TYPES, STATES

service = create_service(OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS)

def get_state_types():
    return service.get(SUB_DOMAIN_STATE_TYPES)

def get_state_type(pk):
    return service.get_detail(SUB_DOMAIN_STATE_TYPES, pk)

def create_state_types(case_type_url):
    state_data = []

    for index, state in enumerate(STATES):
        data = {
            "omschrijving": state,
            "statustekst": state,
            "zaaktype": case_type_url,
            "volgnummer": index + 1,
        }

        data = service.post(SUB_DOMAIN_STATE_TYPES, data)
        state_data.append(data)

    return state_data
