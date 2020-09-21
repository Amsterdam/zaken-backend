import logging
from datetime import datetime

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt
from utils.serializers import (
    DecosJoinFolderFieldsResponseSerializer,
    DecosJoinObjectFieldsResponseSerializer,
    DecosPermitSerializer,
    get_decos_join_mock_folder_fields,
    get_decos_join_mock_object_fields,
)

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
    url = f"https://decosdvl.amsterdam.nl/decosweb/aspx/api/v1/{query}"

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
                "Accept": "application/itemdata",
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
        if not settings.DEBUG:
            url = (
                settings.DECOS_JOIN_API
                + "items/"
                + settings.DECOS_JOIN_BOOK_KNOWN_BAG_OBJECTS
                + f"/COBJECTS?filter=PHONE3 eq '{bag_id}'"
            )

            return self._process_request_to_decos_join(url)
        else:
            return get_decos_join_mock_object_fields()

    def get_folders_with_object_id(self, object_id):
        url = settings.DECOS_JOIN_API + f"items/{object_id}/FOLDERS/"

        return self._process_request_to_decos_join(url)

    def get_documents_with_folder_id(self, folder_id):
        url = settings.DECOS_JOIN_API + f"items/{folder_id}/DOCUMENTS/"
        return self._process_request_to_decos_join(url)

    def _convert_datestring_to_date(self, date_string):
        if "T" in date_string:
            return datetime.strptime(date_string.split("T")[0], "%Y-%m-%d").date()
        return False

    def _get_decos_folder(self, decos_object):
        if not settings.DEBUG:
            try:
                decos_object_id = decos_object["content"][0]["key"]
            except (KeyError, IndexError):
                decos_object_id = False
                response_decos_folder = False

            if decos_object_id:
                response_decos_folder = self.get_folders_with_object_id(decos_object_id)

            if response_decos_folder and response_decos_folder["count"] > 0:
                return response_decos_folder
            return False
        else:
            return get_decos_join_mock_folder_fields()

    def _check_if_permit_is_valid(self, permit):
        premit_date_granted = self._convert_datestring_to_date(permit["date5"])
        permit_status = permit["dfunction"]
        permit_from_date = self._convert_datestring_to_date(permit["date6"])

        if "date7" in permit:
            permit_untill_date = self._convert_datestring_to_date(permit["date7"])

            if (
                permit_from_date
                and premit_date_granted
                and permit_from_date <= datetime.today().date()
                and permit_untill_date >= datetime.today().date()
                and premit_date_granted <= datetime.today().date()
                and permit_status == "Verleend"
            ):
                return True
        else:
            if (
                premit_date_granted
                and premit_date_granted <= datetime.today().date()
                and permit_from_date <= datetime.today().date()
                and permit_status == "Verleend"
            ):
                return True

        # Check if permit is valid today and has been granted

        return False

    def get_checkmarks_by_bag_id(self, bag_id):
        """ Get simple view of the important permits"""
        # TODO Make sure the response goes through a serializer so this doesn't break on KeyError
        response = {
            "has_b_and_b_permit": "UNKNOWN",
            "has_vacation_rental_permit": "UNKNOWN",
        }
        response_decos_obj = self.get_decos_object_with_bag_id(bag_id)

        if response_decos_obj:
            response_decos_folder = self._get_decos_folder(response_decos_obj)

            if response_decos_folder:
                # Only on this moment we can say that
                response["has_b_and_b_permit"] = "False"
                response["has_vacation_rental_permit"] = "False"

                for folder in response_decos_folder["content"]:
                    serializer = DecosJoinFolderFieldsResponseSerializer(
                        data=folder["fields"]
                    )

                    if serializer.is_valid():
                        parent_key = folder["fields"]["parentKey"]

                        if parent_key == settings.DECOS_JOIN_BANDB_ID:
                            response[
                                "has_b_and_b_permit"
                            ] = self._check_if_permit_is_valid(folder["fields"])
                        elif parent_key == settings.DECOS_JOIN_VAKANTIEVERHUUR_ID:
                            response[
                                "has_vacation_rental_permit"
                            ] = self._check_if_permit_is_valid(folder["fields"])
                    else:
                        # assign variable so it is visible in Sentry
                        unexpected_answer = folder["fields"]
                        print(unexpected_answer)
                        logger.error("DECOS JOIN responded with a unexpected answer")

        return response

    def get_permits_by_bag_id(self, bag_id):
        response_decos_obj = self.get_decos_object_with_bag_id(bag_id)
        permits = []

        if response_decos_obj:
            response_decos_folder = self._get_decos_folder(response_decos_obj)

            if response_decos_folder:
                for folder in response_decos_folder["content"]:
                    serializer = DecosJoinFolderFieldsResponseSerializer(
                        data=folder["fields"]
                    )

                    if serializer.is_valid():
                        ser_data = {
                            "permit_granted": self._check_if_permit_is_valid(
                                folder["fields"]
                            ),
                            "processed": folder["fields"]["dfunction"],
                            "date_from": datetime.strptime(
                                folder["fields"]["date6"].split("T")[0], "%Y-%m-%d"
                            ).date(),
                        }
                        parent_key = folder["fields"]["parentKey"]

                        if "date7" in folder["fields"]:
                            ser_data["date_to"] = datetime.strptime(
                                folder["fields"]["date7"].split("T")[0], "%Y-%m-%d"
                            ).date()

                        if parent_key == settings.DECOS_JOIN_BANDB_ID:
                            ser_data[
                                "permit_type"
                            ] = DecosPermitSerializer.PERMIT_B_AND_B
                        elif parent_key == settings.DECOS_JOIN_VAKANTIEVERHUUR_ID:
                            ser_data["permit_type"] = DecosPermitSerializer.PERMIT_VV
                        else:
                            ser_data[
                                "permit_type"
                            ] = DecosPermitSerializer.PERMIT_UNKNOWN

                        permit_serializer = DecosPermitSerializer(data=ser_data)
                        if permit_serializer.is_valid():
                            permits.append(permit_serializer.data)
                        else:
                            p_data = permit_serializer.data
                            print(p_data)
                            logger.error("permit_data is not valid")

                    else:
                        raw_data = folder["fields"]
                        ser_errors = serializer.errors
                        print(raw_data, ser_errors)
                        logger.error("serializer is not valid")
        return permits
