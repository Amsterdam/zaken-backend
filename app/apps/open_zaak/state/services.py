import random
from datetime import datetime

from apps.open_zaak.settings import (
    DOMAIN_CASES,
    OPEN_ZAAK,
    SUB_DOMAIN_STATES,
    SUB_DOMAINS_CASES,
)
from services.service import Service


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

        data = {"datumStatusGezet": str(datetime.now()), **data}

        response = connection.post(data=data)
        return response

    def mock(self, state_types, case_url):
        state_type_url = random.choice(state_types)["url"]

        data = {
            "zaak": case_url,
            "statustype": state_type_url,
            "statustoelichting": "Foo Mock",
        }

        response = self.post(data)
        return response
