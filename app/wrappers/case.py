from wrappers.wrapper import Wrapper
from services.service_cases import CaseService

class Case(Wrapper):
    fields = ('uuid', 'url', 'identificatie', 'omschrijving', 'startdatum', 'einddatum', 'status')
    service = CaseService

    def __init__(self, data):
        super().__init__(data)