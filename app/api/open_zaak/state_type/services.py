from api.open_zaak.settings import OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS, SUB_DOMAIN_STATE_TYPES, STATES
from services.service import Service


class StateTypeService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CATALOGS
    TYPES = SUB_DOMAINS_CATALOGS
    DATA_TYPE = SUB_DOMAIN_STATE_TYPES

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
