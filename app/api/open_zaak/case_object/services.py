from api.open_zaak.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAIN_CASE_OBJECTS, SUB_DOMAINS_CASES
from services.service import Service


class CaseObjectService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CASES
    TYPES = SUB_DOMAINS_CASES
    DATA_TYPE = SUB_DOMAIN_CASE_OBJECTS

    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response

    def post(self, data):
        connection = self.__get_connection__()
        response = connection.post(data=data)
        return response

    def post_address(self, case_url, bag_url):
        data = {
            "zaak": case_url,
            "object": bag_url,
            "objectType": "adres"
        }
        response = self.post(data=data)
        return response

    def mock(self, case_url):
        response = self.post_address(case_url, "https://api.data.amsterdam.nl/bag/v1.1/nummeraanduiding/0363200012086033/")
        return response
