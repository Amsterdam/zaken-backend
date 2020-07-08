from datetime import date

from apps.open_zaak.settings import (
    DOMAIN_CATALOGS,
    OPEN_ZAAK,
    SUB_DOMAIN_CASE_TYPES,
    SUB_DOMAINS_CATALOGS,
)
from services.service import Service


class CaseTypeService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CATALOGS
    TYPES = SUB_DOMAINS_CATALOGS
    DATA_TYPE = SUB_DOMAIN_CASE_TYPES

    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response

    def publish(self, uuid):
        connection = self.__get_connection__()
        response = connection.publish(uuid)
        return response

    def delete(self, uuid):
        connection = self.__get_connection__()
        response = connection.delete(uuid)
        return response

    def mock(self, catalog_url):
        data = {
            "omschrijving": "Illegale vakantieverhuur",
            "vertrouwelijkheidaanduiding": "vertrouwelijk",
            "doel": "Toezicht en handhaving van illegale vakantieverhuur",
            "aanleiding": "Melding of onderzoek",
            "indicatieInternOfExtern": "extern",
            "handelingInitiator": "indienen",
            "onderwerp": "Vakantieverhuur",
            "handelingBehandelaar": "behandelen",
            "doorlooptijd": "P1M",
            "opschortingEnAanhoudingMogelijk": True,
            "verlengingMogelijk": False,
            "publicatieIndicatie": True,
            "productenOfDiensten": [],
            "referentieproces": {"naam": "Nog geen naam"},
            "catalogus": catalog_url,
            "besluittypen": [],
            "gerelateerdeZaaktypen": [],
            "beginGeldigheid": str(date.today()),
            "versiedatum": str(date.today()),
        }
        connection = self.__get_connection__()
        response = connection.post(data=data)
        return response
