from services.wrapper import Wrapper
from api.open_zaak.case.services import CaseService

class Case(Wrapper):
    fields = ('uuid', 'url', 'identificatie', 'omschrijving', 'startdatum', 'einddatum', 'status')
    service = CaseService

    def __init__(self, data):
        super().__init__(data)