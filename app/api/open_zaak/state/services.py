from datetime import datetime
from services.service import Service
from api.open_zaak.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_STATES, SUB_DOMAINS_CASES

class StateService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CASES
    TYPES = SUB_DOMAINS_CASES
    DATA_TYPE = SUB_DOMAIN_STATES

    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response

    def post(self, data):
        connection = self.__get_connection__()

        data = {
          'datumStatusGezet': str(datetime.now()),
          **data
        }
            
        response = connection.post(data=data)
        return response