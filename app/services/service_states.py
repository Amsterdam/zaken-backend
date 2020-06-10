from services.service import Service
from services.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_STATES, SUB_DOMAINS_CASES

class StatesService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CASES
    TYPES = SUB_DOMAINS_CASES
    DATA_TYPE = SUB_DOMAIN_STATES

    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response
