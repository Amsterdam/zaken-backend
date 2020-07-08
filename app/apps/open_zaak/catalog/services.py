from apps.open_zaak.settings import (
    DOMAIN_CATALOGS,
    OPEN_ZAAK,
    ORGANISATION_CONTACT,
    ORGANISATION_DOMAIN,
    ORGANISATION_NAME,
    ORGANISATION_RSIN,
    SUB_DOMAIN_CATALOGS,
    SUB_DOMAINS_CATALOGS,
)
from services.service import Service


class CatalogService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CATALOGS
    TYPES = SUB_DOMAINS_CATALOGS
    DATA_TYPE = SUB_DOMAIN_CATALOGS

    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response

    def mock(self):
        response = self.get()

        if response["count"] > 0:
            return response["results"][0]

        data = {
            "naam": ORGANISATION_NAME,  # Note: naam doesn't seem to be processed and saved
            "domein": ORGANISATION_DOMAIN,
            "rsin": ORGANISATION_RSIN,
            "contactpersoonBeheerNaam": ORGANISATION_CONTACT,
        }
        connection = self.__get_connection__()
        response = connection.post(data=data)
        return response
