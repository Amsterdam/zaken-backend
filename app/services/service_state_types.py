from services.service import Connection, Service
from services.settings import OPEN_ZAAK, DOMAIN, TYPES, SUB_DOMAIN_STATE_TYPES

STATES = [
    'Issuemelding',
    'Onderzoek buitendienst',
    '2de Controle',
    '3de Controle',
    'Hercontrole',
    '2de hercontrole',
    '3de hercontrole',
    'Avondronde',
    'Onderzoek advertentie',
    'Weekend buitendienstonderzoek',
    'Issuemelding'
]

def get_state_types():
    connection = Connection(OPEN_ZAAK)
    service = Service(DOMAIN, TYPES, connection)
    return service.get(SUB_DOMAIN_STATE_TYPES)

def create_state_types(case_type_uri):
    connection = Connection(OPEN_ZAAK)
    service = Service(DOMAIN, TYPES, connection)
    state_data = []

    for index, state in enumerate(STATES):
        data = {
            "omschrijving": state,
            "statustekst": state,
            "zaaktype": case_type_uri,
            "volgnummer": index + 1,
        }

        data = service.post(SUB_DOMAIN_STATE_TYPES, data)
        state_data.append(data)

    return state_data