from services.wrapper import Wrapper
from api.open_zaak.catalog.services import CatalogService

class Catalog(Wrapper):
    fields = ('uuid', 'url', 'zaaktypen')
    service = CatalogService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split('/')[-1]