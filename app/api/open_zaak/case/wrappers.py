from api.open_zaak.case.services import CaseService
from services.wrapper import Wrapper


class Case(Wrapper):
    expand_fields = (
      'status',
    )
    
    fields = (
        'uuid',
        'url',
        'identificatie',
        'omschrijving',
        'toelichting',
        'startdatum',
        'einddatum',
        'status'
        'bronorganisatie',
        'verantwoordelijkeOrganisatie',
        'zaaktype',
        'debug'
    )

    service = CaseService
