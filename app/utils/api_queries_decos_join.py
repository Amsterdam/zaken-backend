import logging

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def get_decos_join_permit():
    try:
        print("Starting Decos Join Request")
        url = (
            "https://decosdvl.acc.amsterdam.nl:443/decosweb/aspx/api/v1/items/90642DCCC2DB46469657C3D0DF0B1ED7/COBJECTS?filter=TEXT8"
            " eq 'Herengracht' and INITIALS eq '1'"
        )
        headers = {"Accept": "application/itemdata"}
        username = settings.DECOS_JOIN_USERNAME
        password = settings.DECOS_JOIN_PASSWORD
        print(url)
        print(headers)
        print(len(username))
        print(len(password))
        response = requests.get(
            url, headers=headers, timeout=5, auth=(username, password)
        )
        print("Response")
        print(response)
        print(response.json())
        return response.json()
    except Exception as e:
        print(e)
    print("Reached here")
    return {}
