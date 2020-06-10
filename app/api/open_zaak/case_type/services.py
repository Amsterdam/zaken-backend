from services.service import Service
from api.open_zaak.settings import OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS, SUB_DOMAIN_CASE_TYPES

class CaseTypeService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CATALOGS
    TYPES = SUB_DOMAINS_CATALOGS
    DATA_TYPE = SUB_DOMAIN_CASE_TYPES

    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response

# from services.service import create_service
# from services.settings import OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS, SUB_DOMAIN_CASE_TYPES
#
# service = create_service(OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS)
#
# def get_case_types():
#     return service.get(SUB_DOMAIN_CASE_TYPES)
#
# def create_case_type(catalog_url):
#     data = {
#         "omschrijving": "Illegale vakantieverhuur",
#         "vertrouwelijkheidaanduiding": "vertrouwelijk",
#         "doel": "Toezicht en handhaving van illegale vakantieverhuur",
#         "aanleiding": "Melding of onderzoek",
#         "indicatieInternOfExtern": "extern",
#         "handelingInitiator": "indienen",
#         "onderwerp": "Vakantieverhuur",
#         "handelingBehandelaar": "behandelen",
#         "doorlooptijd": "P1M",
#         "opschortingEnAanhoudingMogelijk": True,
#         "verlengingMogelijk": False,
#         "publicatieIndicatie": True,
#         "productenOfDiensten": [],
#         "referentieproces": {
#             "naam": "Nog geen naam"
#         },
#         "catalogus": catalog_url,
#         "besluittypen": [],
#         "gerelateerdeZaaktypen": [],
#         "beginGeldigheid": "2020-05-28",
#         "versiedatum": "2020-05-28"
#     }
#
#     case_type = service.post(SUB_DOMAIN_CASE_TYPES, data)
#     return case_type
#
#
# def publish_case_type(url):
#     case_type = service.publish(url)
#     return case_type
#
# def delete_case_type(url):
#     response = service.delete(url)
#     return response
#
# def get_case_type(url):
#     response = service.get(url)
#     return response