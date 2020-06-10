from services.service import Service
from api.open_zaak.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAINS_CASES, SUB_DOMAIN_CASES, ORGANISATION_RSIN

class CaseService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CASES
    TYPES = SUB_DOMAINS_CASES
    DATA_TYPE = SUB_DOMAIN_CASES

    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response

    def post(self, zaaktype, startdatum, omschrijving):
        connection = self.__get_connection__()

        data = {
            'bronorganisatie': ORGANISATION_RSIN,
            'verantwoordelijkeOrganisatie': ORGANISATION_RSIN,
            'startdatum': startdatum,
            'omschrijving': omschrijving,
            'zaaktype': zaaktype
        }

        response = connection.post(data={
            'bronorganisatie': ORGANISATION_RSIN,
            'verantwoordelijkeOrganisatie': ORGANISATION_RSIN,
            'startdatum': startdatum,
            'omschrijving': omschrijving,
            'zaaktype': zaaktype
        })

        return response

    def delete(self, uuid):
        connection = self.__get_connection__()
        response = connection.delete(uuid)
        return response
