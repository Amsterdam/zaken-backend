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
        'zaaktype',
        'debug'
    )

    service = CaseService

