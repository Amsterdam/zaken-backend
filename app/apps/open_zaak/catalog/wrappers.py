from apps.open_zaak.catalog.services import CatalogService
from services.wrapper import Wrapper


class Catalog(Wrapper):
    fields = ('uuid', 'url', 'zaaktypen')
    service = CatalogService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split('/')[-1]
