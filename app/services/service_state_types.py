from app.services.service import create_service
from app.services.settings import OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS, SUB_DOMAIN_STATE_TYPES, STATES

service = create_service(OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS)


def get_state_types():
    return service.get(SUB_DOMAIN_STATE_TYPES)


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
