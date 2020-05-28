import os

OPEN_ZAAK = 'openzaak'
DOMAIN = 'catalogi'
SUB_DOMAIN_CATALOGS = 'catalogussen'
SUB_DOMAIN_CASE_TYPES = 'zaaktypen'
SUB_DOMAIN_STATE_TYPES = 'statustypen'

TYPES = [SUB_DOMAIN_CATALOGS, SUB_DOMAIN_CASE_TYPES, SUB_DOMAIN_STATE_TYPES]

CONNECTIONS = {
    OPEN_ZAAK:  {
            'host': os.environ['OPEN_ZAAK_CONTAINER_NAME'],
            'port': os.environ['OPEN_ZAAK_PORT'],
            'api_version': os.environ['OPEN_ZAAK_API_VERSION'],
            'client': os.environ['OPEN_ZAAK_CLIENT'],
            'secret_key': os.environ['OPEN_ZAAK_SECRET_KEY']
        }
}

