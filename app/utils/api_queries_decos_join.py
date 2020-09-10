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
# "TEXT8 eq 'Herengracht' and INITIALS eq '1'"
# book_id="90642DCCC2DB46469657C3D0DF0B1ED7"

# Bag id:
# PHONE eq ''

# Objectboeken:
# BAG Objecten: 90642DCCC2DB46469657C3D0DF0B1ED7
# Objecten onbekend: B1FF791EA9FA44698D5ABBB1963B94EC
def get_decos_join_permit(query, book_id):

    print("Starting Decos Join Request")
    url = f"https://decosdvl.acc.amsterdam.nl:443/decosweb/aspx/api/v1/items/{book_id}/COBJECTS?filter={query}"

    # Root
    data = generic_decos_request(url)

    # Nested Items
    items = data.get("links", [])
    items_urls = [item.get("href") for item in items]
    data_items = [generic_decos_request(url) for url in items_urls]

    return {"root": data, "items": data_items}


def get_decos_join_request(query):
    print("Starting Decos Join Request")
    url = f"https://decosdvl.acc.amsterdam.nl:443/decosweb/aspx/api/v1/{query}"

    data = generic_decos_request(url)

    # Nested Items
    # items = data.get("links", [])
    # items_urls = [item.get("href") for item in items]
    # data_items = [generic_decos_request(url) for url in items_urls]

    return {"root": data}


def get_decos_join_request_swagger(query):
    print("Starting Decos Join Request")
    url = f"https://decosdvl.amsterdam.nl:443/decosweb/aspx/api/v1/{query}"

    headers = {"Accept": "application/itemdata"}
    username = settings.DECOS_JOIN_USERNAME
    password = settings.DECOS_JOIN_PASSWORD
    response = requests.get(url, headers=headers, timeout=8, auth=(username, password))

    # Nested Items
    # items = data.get("links", [])
    # items_urls = [item.get("href") for item in items]
    # data_items = [generic_decos_request(url) for url in items_urls]

    return response


class DecosJoinRequest:
    """
    Object to connect to decos join and retrieve permits
    """

    def _process_request_to_decos_join(self, url):
        try:
            username = settings.DECOS_JOIN_USERNAME
            password = settings.DECOS_JOIN_PASSWORD
            headers = {
                "Accept": "application/json",
                "content-type": "application/json",
            }

            response = requests.get(
                url, headers=headers, timeout=8, auth=(username, password)
            )

            return response.json()
        except requests.exceptions.Timeout:
            return False

    def get_decos_object_with_address(self, address):
        url = (
            settings.DECOS_JOIN_API
            + "items/"
            + settings.DECOS_JOIN_BOOK_KNOWN_BAG_OBJECTS
            + f"/COBJECTS?filter=SUBJECT1 eq '{address}'"
        )

        return self._process_request_to_decos_join(url)

    def get_decos_object_with_bag_id(self, bag_id):
        url = (
            settings.DECOS_JOIN_API
            + "items/"
            + settings.DECOS_JOIN_BOOK_KNOWN_BAG_OBJECTS
            + f"/COBJECTS?filter=PHONE3 eq '{bag_id}'"
        )

        return self._process_request_to_decos_join(url)

    def get_folders_with_object_id(self, object_id):
        url = settings.DECOS_JOIN_API + f"items/{object_id}/FOLDERS/"

        return self._process_request_to_decos_join(url)

    def get_documents_with_folder_id(self, folder_id):
        url = settings.DECOS_JOIN_API + f"items/{folder_id}/DOCUMENTS/"
        return self._process_request_to_decos_join(url)

    def get_checkmarks_with_bag_id(self, bag_id):
        """ Get simple view """
        response = {"has_b_and_b_permit": False, "has_vacation_rental_permit": False}
        response_decos_obj = self.get_decos_object_with_bag_id(bag_id)

        if response_decos_obj and response_decos_obj["count"] > 0:
            response_decos_folder = self.get_folders_with_object_id(
                response_decos_obj["content"][0]["key"]
            )

            if response_decos_folder and response_decos_folder["count"] > 0:
                for folder in response_decos_folder["content"]:
                    parent_key = folder["fields"]["parentKey"]
                    if parent_key == settings.DECOS_JOIN_BANDB_ID:
                        response["has_b_and_b_permit"] = True
                    if parent_key == settings.DECOS_JOIN_VAKANTIEVERHUUR_ID:
                        response["has_vacation_rental_permit"] = True

        return response
