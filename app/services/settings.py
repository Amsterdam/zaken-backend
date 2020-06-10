import os
from api.open_zaak.settings import OPEN_ZAAK

CONNECTIONS = {
    OPEN_ZAAK: {
        'host': os.environ['OPEN_ZAAK_CONTAINER_NAME'],
        'port': os.environ['OPEN_ZAAK_PORT'],
        'api_version': os.environ['OPEN_ZAAK_API_VERSION'],
        'client': os.environ['OPEN_ZAAK_CLIENT'],
        'secret_key': os.environ['OPEN_ZAAK_SECRET_KEY']
    }
}
