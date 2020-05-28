from services.service import Connection, Service
from services.settings import OPEN_ZAAK, DOMAIN, TYPES, SUB_DOMAIN_CATALOGS

def get_catalogs():
    connection = Connection(OPEN_ZAAK)
    service = Service(DOMAIN, TYPES, connection)
    return service.get(SUB_DOMAIN_CATALOGS)

def create_catalog():
    connection = Connection(OPEN_ZAAK)
    service = Service(DOMAIN, TYPES, connection)
    data = {
        "naam": "Hello",
        "domein": "WONEN",
        "rsin": "221222558", # Just a randomly generated id for now (https://www.testnummers.nl/)
        "contactpersoonBeheerNaam": "Beheerder Wonen",
    }

    return service.post(SUB_DOMAIN_CATALOGS, data)

