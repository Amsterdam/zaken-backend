from datetime import date

from api.open_zaak.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAINS_CASES, SUB_DOMAIN_CASES, ORGANISATION_RSIN
from services.service import Service


class CaseService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CASES
    TYPES = SUB_DOMAINS_CASES
    DATA_TYPE = SUB_DOMAIN_CASES

    def get(self, uuid=None, params=None):
        connection = self.__get_connection__()
        response = connection.get(uuid=uuid, params=params)

        return response

    def post(self, data):
        connection = self.__get_connection__()
        organisation_data = {
            'bronorganisatie': ORGANISATION_RSIN,
            'verantwoordelijkeOrganisatie': ORGANISATION_RSIN,
        }
        all_data = {**data, **organisation_data}
        response = connection.post(data=all_data)

        return response

    def delete(self, uuid):
        connection = self.__get_connection__()
        response = connection.delete(uuid)
        return response

    def update(self, uuid, data):
        connection = self.__get_connection__()
        organisation_data = {
            'bronorganisatie': ORGANISATION_RSIN,
            'verantwoordelijkeOrganisatie': ORGANISATION_RSIN,
        }
        all_data = {**data, **organisation_data}
        response = connection.put(uuid, all_data)
        return response

    def mock(self, case_type_url):
        responses = []
        for i in range(4):
            data = {
                "omschrijving": "Hello World",
                "startdatum": str(date.today()),
                "einddatum": str(date.today()),
                "zaaktype": case_type_url,
            }
            response = self.post(data)
            responses.append(response)

        return responses
