from services.service import Service
from services.settings import OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS, SUB_DOMAIN_STATE_TYPES

class StateTypesService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CATALOGS
    TYPES = SUB_DOMAINS_CATALOGS
    DATA_TYPE = SUB_DOMAIN_STATE_TYPES

    def get(self, pk=None):
        connection = self.__get_connection__()
        response = connection.get(pk)
        return response
