from services.service import create_service
from services.settings import OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS, SUB_DOMAIN_CATALOGS, ORGANISATION_RSIN

service = create_service(OPEN_ZAAK, DOMAIN_CATALOGS, SUB_DOMAINS_CATALOGS)

def get_catalogs():
    return service.get(SUB_DOMAIN_CATALOGS)

def create_catalog():
    data = {
        "naam": "Hello",
        "domein": "WONEN",
        "rsin": ORGANISATION_RSIN,
        "contactpersoonBeheerNaam": "Beheerder Wonen",
    }

    return service.post(SUB_DOMAIN_CATALOGS, data)
