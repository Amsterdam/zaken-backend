from services.wrapper import Wrapper
from api.open_zaak.case.services import CaseService

class Case(Wrapper):
    fields = (
        'uuid',
        'url',
        'identificatie',
        'omschrijving',
        'startdatum',
        'einddatum',
        'status'
        'bronorganisatie',
        'verantwoordelijkeOrganisatie',
        'zaaktype'
    )
    service = CaseService

    def __init__(self, data):
        super().__init__(data)

    def create(self):
        service = self.service()
        response = service.post(self.zaaktype, self.startdatum, self.omschrijving)
        self.__set_data__(response)