import os

CONNECTIONS = {
    "openzaak": {
        "host": os.environ.get("OPEN_ZAAK_CONTAINER_HOST", ""),
        "port": os.environ.get("OPEN_ZAAK_PORT", ""),
        "api_version": os.environ.get("OPEN_ZAAK_API_VERSION", ""),
        "client": os.environ.get("OPEN_ZAAK_CLIENT", ""),
        "secret_key": os.environ.get("OPEN_ZAAK_SECRET_KEY", ""),
    }
}
