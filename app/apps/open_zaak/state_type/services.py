from apps.open_zaak.settings import (
    DOMAIN_CATALOGS,
    OPEN_ZAAK,
    STATES,
    SUB_DOMAIN_STATE_TYPES,
    SUB_DOMAINS_CATALOGS,
)
from services.service import Service


class OpenZaakStateTypeService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CATALOGS
    TYPES = SUB_DOMAINS_CATALOGS
    DATA_TYPE = SUB_DOMAIN_STATE_TYPES

    # TODO: rewrite
    def get_state_type(self, state_type):
        states = self.get()["results"]
        for state in states:
            if state["statustekst"] == state_type:
                return state

    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response

    def mock(self, zaaktype_url):
        connection = self.__get_connection__()
        responses = []
        for index, state in enumerate(STATES):
            data = {
                "omschrijving": state,
                "statustekst": state,
                "zaaktype": zaaktype_url,
                "volgnummer": index + 1,
            }
            response = connection.post(data=data)
            responses.append(response)

        return responses
