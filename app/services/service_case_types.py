from services.service import Connection, Service
from services.settings import OPEN_ZAAK, DOMAIN, TYPES, SUB_DOMAIN_CASE_TYPES

def get_case_types():
    connection = Connection(OPEN_ZAAK)
    service = Service(DOMAIN, TYPES, connection)
    return service.get(SUB_DOMAIN_CASE_TYPES)

def create_case_type(catalog_uri):
    connection = Connection(OPEN_ZAAK)
    service = Service(DOMAIN, TYPES, connection)
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
        "referentieproces": {
            "naam": "Nog geen naam"
        },
        "catalogus": catalog_uri,
        "besluittypen": [],
        "gerelateerdeZaaktypen": [],
        "beginGeldigheid": "2020-05-28",
        "versiedatum": "2020-05-28"
    }

    return service.post(SUB_DOMAIN_CASE_TYPES, data)