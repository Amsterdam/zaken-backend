import os

from apps.open_zaak.settings import OPEN_ZAAK

CONNECTIONS = {
    OPEN_ZAAK: {
        "host": os.environ.get("OPEN_ZAAK_CONTAINER_NAME", ""),
        "port": os.environ.get("OPEN_ZAAK_PORT", ""),
        "api_version": os.environ.get("OPEN_ZAAK_API_VERSION", ""),
        "client": os.environ.get("OPEN_ZAAK_CLIENT", ""),
        "secret_key": os.environ.get("OPEN_ZAAK_SECRET_KEY", ""),
    }
}
