from apps.open_zaak.case_type.services import CaseTypeService
from services.wrapper import Wrapper


class CaseType(Wrapper):
    fields = ('url', 'uuid', 'omschrijving', 'doel', 'aanleiding', 'onderwerp')
    service = CaseTypeService

    def __init__(self, data):
        super().__init__(data)
        self.uuid = self.url.split('/')[-1]
