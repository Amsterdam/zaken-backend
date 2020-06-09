from services.service import create_connection
from services.settings import OPEN_ZAAK

connection = create_connection(OPEN_ZAAK)


def get_object(object_url):
    return connection.get(object_url)
