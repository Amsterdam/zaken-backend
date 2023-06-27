import logging
import re
from datetime import datetime

import requests
from apps.permits.mocks import (
    get_decos_join_mock_folder_fields_address_a,
    get_decos_join_mock_object_fields,
)
from apps.permits.serializers import PermitSerializer
from django.conf import settings

logger = logging.getLogger(__name__)


class DecosJoinConf:
    PERMIT_TYPE = "permit_type"
    DECOS_JOIN_BOOK_KEY = "decos_join_book_key"
    EXPRESSION_STRING = "expression_string"
    INITIAL_DATA = "initial_data"
    FIELD_MAPPING = "field_mapping"

    def __init__(self):
        self.conf = []
        self.default_expression = "bool()"
        self.default_initial_data = {}
        self.default_field_mapping = {}

    def __len__(self):
        return len(self.conf)

    def __iter__(self):
        for c in self.conf:
            yield c

    def add_conf(self, conf):
        new_conf = []
        try:
            for p in conf:
                if len(p) >= 2:
                    new_conf.append(
                        {
                            self.DECOS_JOIN_BOOK_KEY: str(p[0]),
                            self.PERMIT_TYPE: str(p[1]),
                            self.EXPRESSION_STRING: str(p[2])
                            if len(p) >= 3
                            else self.default_expression,
                            self.INITIAL_DATA: dict(p[3])
                            if len(p) >= 4
                            else self.default_initial_data,
                            self.FIELD_MAPPING: p[4]
                            if len(p) >= 5
                            else self.default_field_mapping,
                        }
                    )
        except Exception as e:
            logger.error("Decos Join config invalid format")
            logger.error(str(e))
        if new_conf:
            self.conf = []
            for c in new_conf:
                self.conf.append(c)

    def map_data_on_conf_keys(self, data, conf):
        if not conf:
            return {}
        return dict(
            (conf.get(self.FIELD_MAPPING).get(k), v)
            for k, v in data.items()
            if k in list(conf.get(self.FIELD_MAPPING, {}).keys())
        )

    def datestring_to_timestamp(self, datestring):
        if type(datestring) == str and re.match(
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", datestring
        ):
            return datetime.timestamp(
                datetime.strptime(datestring.split("T")[0], "%Y-%m-%d")
            )
        return datestring

    def clean_data(self, data):
        if not data:
            return {}
        return dict((k, self.datestring_to_timestamp(v)) for k, v in data.items())

    def expression_is_valid(self, data_to_validate, conf, dt):
        data = {}
        if not conf or not dt:
            return False
        data.update(conf.get(self.INITIAL_DATA, {}))
        data.update(self.clean_data(data_to_validate))
        data.update(
            {
                "ts_now": datetime.timestamp(
                    datetime(dt.year, dt.month, dt.day, 0, 0, 0)
                ),
            }
        )
        base_str = conf.get(self.EXPRESSION_STRING)
        base_str = base_str if base_str else "bool()"
        try:
            compare_str = base_str.format(**data)
        except Exception as e:
            compare_str = base_str
            logger.error("Error valid data mapping")
            logger.error(str(e))
            return False
        try:
            valid = eval(compare_str)
        except Exception as e:
            logger.error("Error valid expression evaluation")
            logger.error(str(e))
            return False
        return valid

    def set_default_expression(self, expression_str):
        self.default_expression = expression_str

    def set_default_initial_data(self, initial_data_dict):
        self.default_initial_data = initial_data_dict

    def set_default_field_mapping(self, field_mapping_dict):
        self.default_field_mapping = field_mapping_dict

    def get_conf_by_book_key(self, book_key):
        for p in self:
            if p.get(self.DECOS_JOIN_BOOK_KEY) == book_key:
                return p

    def get_book_keys(self):
        return [v.get(self.DECOS_JOIN_BOOK_KEY) for v in self]


class DecosJoinRequest:
    """
    Object to connect to decos join and retrieve permits
    """

    def get(self, path=""):
        url = "%s%s" % (settings.DECOS_JOIN_API, path)
        return self._process_request_to_decos_join(url)

    def _process_request_to_decos_join(self, url):
        try:
            headers = {
                "Accept": "application/itemdata",
                "content-type": "application/json",
            }
            request_params = {
                "headers": headers,
                "timeout": 30,
            }

            if settings.DECOS_JOIN_AUTH_BASE64:
                request_params["headers"].update(
                    {
                        "Authorization": f"Basic {settings.DECOS_JOIN_AUTH_BASE64}",
                    }
                )

            logger.info(url)

            response = requests.get(url, **request_params, verify=False)

            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Request to Decos Join timed out")
            return False
        except Exception as e:
            logger.error("Decos Join connection failed")
            logger.error(str(e))
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
        if not settings.USE_DECOS_MOCK_DATA:
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
        url = (
            settings.DECOS_JOIN_API
            + f"items/{object_id}/FOLDERS/?properties=false&fetchParents=false&oDataQuery.top=100"
        )

        return self._process_request_to_decos_join(url)

    def get_documents_with_folder_id(self, folder_id):
        url = settings.DECOS_JOIN_API + f"items/{folder_id}/DOCUMENTS/"
        return self._process_request_to_decos_join(url)

    def _get_decos_folder(self, decos_object):
        if not settings.USE_DECOS_MOCK_DATA:
            response_decos_folder = {}
            try:
                #  Get all Decos object id's
                list_of_decos_object_ids = [
                    obj["key"] for obj in decos_object["content"]
                ]
            except (KeyError, IndexError):
                list_of_decos_object_ids = []

            if len(list_of_decos_object_ids) > 0:
                #  Get all folders for every id and merge them.
                for decos_object_id in list_of_decos_object_ids:
                    folder_with_object_id = self.get_folders_with_object_id(
                        decos_object_id
                    )
                    object_id_folder = (
                        folder_with_object_id if folder_with_object_id else {}
                    )
                    response_decos_folder["count"] = response_decos_folder.get(
                        "count", 0
                    ) + object_id_folder.get("count", 0)
                    response_decos_folder["content"] = [
                        *response_decos_folder.get("content", []),
                        *object_id_folder.get("content", []),
                    ]

            if response_decos_folder and response_decos_folder.get("count", 0) > 0:
                return response_decos_folder
            return False
        else:
            return get_decos_join_mock_folder_fields_address_a()

    def get_decos_entry_by_bag_id(self, bag_id, dt):
        """Get simple view of the important permits"""

        response = {}

        decos_join_conf_object = DecosJoinConf()
        decos_join_conf_object.set_default_expression(
            settings.DECOS_JOIN_DEFAULT_PERMIT_VALID_EXPRESSION
        )
        decos_join_conf_object.set_default_initial_data(
            settings.DECOS_JOIN_DEFAULT_PERMIT_VALID_INITIAL_DATA
        )
        decos_join_conf_object.set_default_field_mapping(
            settings.DECOS_JOIN_DEFAULT_FIELD_MAPPING
        )

        decos_join_conf_object.add_conf(settings.DECOS_JOIN_DEFAULT_PERMIT_VALID_CONF)

        permits = [
            {
                "permit_granted": "UNKNOWN",
                "permit_type": v.get(DecosJoinConf.PERMIT_TYPE),
            }
            for v in decos_join_conf_object
        ]

        response_decos_obj = self.get_decos_object_with_bag_id(bag_id)

        response_decos_folder = {}
        if response_decos_obj:
            response_decos_folder = self._get_decos_folder(response_decos_obj)
            if response_decos_folder:

                # permits
                for folder in response_decos_folder["content"]:

                    parent_key = folder.get("fields", {}).get("parentKey")
                    if parent_key in decos_join_conf_object.get_book_keys():
                        data = {}
                        conf = decos_join_conf_object.get_conf_by_book_key(parent_key)
                        permit_granted = decos_join_conf_object.expression_is_valid(
                            folder["fields"], conf, dt
                        )
                        data.update(
                            {
                                "permit_granted": "GRANTED"
                                if permit_granted
                                else "NOT_GRANTED",
                                "permit_type": conf.get(DecosJoinConf.PERMIT_TYPE),
                                "raw_data": folder["fields"],
                                "details": decos_join_conf_object.map_data_on_conf_keys(
                                    folder["fields"], conf
                                ),
                            }
                        )
                        permit_serializer = PermitSerializer(data=data)
                        if permit_serializer.is_valid():
                            for d in permits:
                                if d.get("permit_type") == conf.get(
                                    DecosJoinConf.PERMIT_TYPE
                                ):
                                    current_permit_raw_data = d.get("raw_data", {})
                                    # Check all Decos folders. Multiple permits are possible. Which one do you want to show?
                                    # Check if there's already a permit saved with the same permit type AND raw data. Else: save this permit.
                                    if current_permit_raw_data:
                                        # Current permit data found so check which one is valid now.
                                        now = datetime.now().isoformat()
                                        next_permit_raw_data = (
                                            permit_serializer.data.get("raw_data", {})
                                        )
                                        next_permit_valid_from = (
                                            next_permit_raw_data.get("date6")
                                        )
                                        next_permit_valid_until = (
                                            next_permit_raw_data.get("date7")
                                        )
                                        current_permit_valid_from = (
                                            current_permit_raw_data.get("date6")
                                        )
                                        current_permit_valid_until = (
                                            current_permit_raw_data.get("date7")
                                        )

                                        # Wrap datetime validation in a try-catch to prevent breaking code.
                                        try:
                                            # Is the current permit valid/active? => now must be between start and enddate.
                                            is_current_permit_valid = (
                                                current_permit_valid_from <= now
                                                and now <= current_permit_valid_until
                                            )

                                            # Is the next permit valid/active? => now must be between start and enddate.
                                            is_next_permit_valid = (
                                                next_permit_valid_from <= now
                                                and now <= next_permit_valid_until
                                            )

                                            if is_next_permit_valid:
                                                # Next permit is valid so this is the one users would like to see. Update permit data.
                                                d.update(permit_serializer.data)
                                            elif not is_current_permit_valid:
                                                # Current permit and next permit are not valid.
                                                if next_permit_valid_from > now:
                                                    # There's a future permit so show this to the user.
                                                    # This does not cover a use case with both current permit and next permit in the future.
                                                    # This is not a realistic use case because multiple future permits will not be issued.
                                                    d.update(permit_serializer.data)
                                                elif (
                                                    next_permit_valid_from
                                                    > current_permit_valid_from
                                                ):
                                                    # Both permits are expired so show most recent one.
                                                    d.update(permit_serializer.data)

                                        except Exception as e:
                                            logger.error(
                                                f"Decos permits could not validate datetimes: {e}"
                                            )

                                    else:
                                        # There's NO permit with raw data so update.
                                        d.update(permit_serializer.data)

                    else:
                        logger.error("DECOS JOIN parent key not found in config")
                        logger.info("book key: %s" % parent_key)
                        logger.info(
                            "permit name: %s" % folder.get("fields", {}).get("text45")
                        )
                        logger.info(
                            "permit result: %s"
                            % folder.get("fields", {}).get("dfunction")
                        )
                        logger.info(
                            "Config keys: %s" % decos_join_conf_object.get_book_keys()
                        )

        response.update(
            {
                "permits": permits,
                "decos_folders": response_decos_folder,
            }
        )

        return response
