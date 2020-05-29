from services.service import create_service
from services.settings import OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAINS_CASES, SUB_DOMAIN_CASES, ORGANISATION_RSIN

service = create_service(OPEN_ZAAK, DOMAIN_CASES, SUB_DOMAINS_CASES)

def get_cases():
    return service.get(SUB_DOMAIN_CASES)

def create_case(case_type_uri):
    data = {
        'bronorganisatie': ORGANISATION_RSIN,
        'omschrijving': 'HELLO WORLD OMSCHRIJVING',
        'verantwoordelijkeOrganisatie': ORGANISATION_RSIN,
        'zaaktype': case_type_uri,
        'startdatum': '2020-05-28'
    }

    return service.post(SUB_DOMAIN_CASES, data)

