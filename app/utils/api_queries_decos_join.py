import logging

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def generic_decos_request(url):
    try:
        headers = {"Accept": "application/itemdata"}
        username = settings.DECOS_JOIN_USERNAME
        password = settings.DECOS_JOIN_PASSWORD
        response = requests.get(
            url, headers=headers, timeout=8, auth=(username, password)
        )
        data = response.json()
        return data
    except Exception as e:
        print(e)

    return {}


# Straat + huisnummer
# MAILADDRESS

# Postcode
# ZIPCODE

# Verblijsobjectidentificatie
# PHONE

# Ligplaatsidentificatie
# Text11

# Straat
# TEXT8

# Huisnummer
# INITIALS

# Letter
# FAX1

# Toevoeging
# PHONE2

# Example parameters:
# query="TEXT8 eq 'Herengracht' and INITIALS eq '1'"
# book_id="90642DCCC2DB46469657C3D0DF0B1ED7"

# Objectboeken:
# BAG Objecten: 90642DCCC2DB46469657C3D0DF0B1ED7
# Objecten onbekend: B1FF791EA9FA44698D5ABBB1963B94EC
def get_decos_join_permit(query, book_id):

    print("Starting Decos Join Request")
    url = f"https://decosdvl.acc.amsterdam.nl:443/decosweb/aspx/api/v1/items/{book_id}/COBJECTS?filter={query}"

    data = generic_decos_request(url)
    print("First request")
    print(data)
    items = data.get("links", [])
    items_urls = [item.get("href") for item in items]
    print("Nested items urls")
    print(items_urls)
    data_items = [generic_decos_request(url) for url in items_urls]
    print("All data items")
    print(data_items)
    return {"items": data_items}
