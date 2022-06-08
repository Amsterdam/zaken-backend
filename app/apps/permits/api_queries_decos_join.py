import logging
import re
from datetime import datetime, timedelta

import requests
from apps.permits.mocks import (
    get_decos_join_mock_folder_fields,
    get_decos_join_mock_object_fields,
)
from apps.permits.serializers import (
    DecosVakantieverhuurReportSerializer,
    PermitSerializer,
)
from django.conf import settings

logger = logging.getLogger(__name__)


class VakantieverhuurReports:
    def __init__(self, *args, **kwargs):
        self.report_id = kwargs.get("report_id")
        self.cancellation_id = kwargs.get("cancellation_id")
        self.days = []
        self.days_removed = []

    def add_raw_data(self, data):
        if settings.USE_DECOS_MOCK_DATA:
            data = get_decos_join_mock_folder_fields().get("content", [])
        if not self.report_id or not self.cancellation_id:
            return
        data = [
            dd.data
            for dd in [
                DecosVakantieverhuurReportSerializer(
                    data=dict(
                        **f["fields"],
                        **{
                            "is_cancellation": f.get("fields", {}).get("parentKey")
                            == self.cancellation_id
                        },
                    )
                )
                for f in data
                if f.get("fields", {}).get("parentKey")
                in [
                    self.report_id,
                    self.cancellation_id,
                ]
            ]
            if dd.is_valid()
        ]
        self.add_data(data)

    def add_data(self, data):
        serializer = DecosVakantieverhuurReportSerializer(data=data, many=True)
        if serializer.is_valid():
            data = sorted(serializer.data, key=lambda k: k["sequence"])
            for d_set in data:
                d = {
                    "report_date": datetime.strptime(
                        d_set["document_date"].split("T")[0], "%Y-%m-%d"
                    ),
                    "check_in_date": datetime.strptime(
                        d_set["date6"].split("T")[0], "%Y-%m-%d"
                    ),
                    "check_out_date": datetime.strptime(
                        d_set["date7"].split("T")[0], "%Y-%m-%d"
                    ),
                    "is_cancellation": d_set["is_cancellation"],
                }
                self.add_report(**d)
            return True
        return False

    def add_report(self, report_date, check_in_date, check_out_date, is_cancellation):
        day = timedelta(days=1)
        report_set = [[], report_date, is_cancellation]
        while check_in_date < check_out_date:
            report_set[0].append(check_in_date)
            check_in_date = check_in_date + day
        if report_set[0]:
            self.days.append(report_set)

    def get_set_by_year(self, year, today):
        o = {}
        day = timedelta(days=1)
        today = datetime.strptime(today.strftime("%Y-%m-%d"), "%Y-%m-%d")
        reports = [
            {
                "is_cancellation": d_set[2],
                "report_date": d_set[1],
                "check_in_date": d_set[0][0],
                "check_out_date": d_set[0][-1] + day,
            }
            for d_set in self.days
            if d_set[0][0].year == year or (d_set[0][-1] + day).year == year
        ]
        reports.reverse()
        o.update(self._rented(year, today))
        o.update(
            {
                "reports": reports,
                "year": year,
            }
        )
        return o

    def all_years(self, today):
        years = []
        if not self.days:
            return []
        this_year = datetime.today().year
        start_year = sorted(self.days, key=lambda d: d[1])[0][1].year
        for year in range(start_year, this_year + 1):
            year_reports = self.get_set_by_year(year, today)
            if year_reports.get("reports") or year == this_year:
                years.append(year_reports)
        return years

    def _days_flat(self, days):
        return [d for d_set in days for d in d_set[0]]

    def _rented(self, year, today):
        valid_days = []
        for d_set in self.days:
            for d in d_set[0]:
                if d.year == year and not d_set[2]:
                    if d not in valid_days:
                        valid_days.append(d)
                elif d.year == year and d_set[2]:
                    if d in valid_days:
                        valid_days.remove(d)

        is_rented_today = bool(today in valid_days)
        rented_days = [d for d in valid_days if d < today]
        planned_days = [d for d in valid_days if d >= today]
        return {
            "rented_days_count": len(rented_days),
            "planned_days_count": len(planned_days),
            "is_rented_today": is_rented_today,
        }


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

            response = requests.get(url, **request_params)

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
        url = settings.DECOS_JOIN_API + f"items/{object_id}/FOLDERS/"

        return self._process_request_to_decos_join(url)

    def get_documents_with_folder_id(self, folder_id):
        url = settings.DECOS_JOIN_API + f"items/{folder_id}/DOCUMENTS/"
        return self._process_request_to_decos_join(url)

    def _get_decos_folder(self, decos_object):
        if not settings.USE_DECOS_MOCK_DATA:
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

        vakantieverhuur_reports = VakantieverhuurReports(
            **{
                "report_id": settings.DECOS_JOIN_VAKANTIEVERHUUR_MELDINGEN_ID,
                "cancellation_id": settings.DECOS_JOIN_VAKANTIEVERHUUR_AFMELDINGEN_ID,
            }
        )

        response_decos_obj = self.get_decos_object_with_bag_id(bag_id)

        if response_decos_obj:
            response_decos_folder = self._get_decos_folder(response_decos_obj)
            if response_decos_folder:

                # vakantieverhuur reports
                vakantieverhuur_reports.add_raw_data(response_decos_folder["content"])

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
                "vakantieverhuur_reports": vakantieverhuur_reports.all_years(
                    datetime.today()
                ),
            }
        )

        return response
