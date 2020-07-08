from datetime import datetime
from apps.open_zaak.settings import OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS, SUB_DOMAIN_INFORMATION_OBJECT_TYPE
from services.service import Service

ACTION_CHECKED_CASE = 'Toezichthouder actie'

class InformationObjectTypeService(Service):
    NAME = OPEN_ZAAK
    DOMAIN = DOMAIN_CATALOGS
    TYPES = SUB_DOMAINS_CATALOGS
    DATA_TYPE = SUB_DOMAIN_INFORMATION_OBJECT_TYPE

    def delete(self, uuid):
        connection = self.__get_connection__()
        response = connection.delete(uuid)
        return response
        
    def get(self, uuid=None):
        connection = self.__get_connection__()
        response = connection.get(uuid)
        return response

    def publish(self, uuid):
        connection = self.__get_connection__()
        response = connection.publish(uuid)
        return response

    def post(self, catalog_url, description):
        data = {
            'catalogus': catalog_url,
            'omschrijving': description,
            'vertrouwelijkheidaanduiding': 'vertrouwelijk',
            'beginGeldigheid':  str(datetime.now().date()),
        }
        connection = self.__get_connection__()
        response = connection.post(data=data)
        return response

    def mock(self, catalog_url):
        return self.post(catalog_url, ACTION_CHECKED_CASE)