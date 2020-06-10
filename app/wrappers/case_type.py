from wrappers.wrapper import Wrapper
from services.service_case_types import CaseTypesService

class CaseType(Wrapper):
    fields = ('url', 'uuid', 'omschrijving', 'doel', 'aanleiding', 'onderwerp')
    service = CaseTypesService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split('/')[-1]