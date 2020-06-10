from wrappers.wrapper import Wrapper
from services.service_catalogs import CatalogsService

class Catalog(Wrapper):
    fields = ('uuid', 'url', 'zaaktypen')
    service = CatalogsService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split('/')[-1]