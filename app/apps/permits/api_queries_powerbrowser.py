import logging
import os

import requests
from apps.permits.serializers import PowerbrowserSerializer
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

BED_AND_BREAKFAST_PRODUCT = "bed en breakfast"


def is_valid_bed_and_breakfast_permit(permit, reference_dt=None):
    if reference_dt is None:
        reference_dt = timezone.now()

    if not _contains_bed_and_breakfast_marker(permit):
        return False

    result = (permit.get("resultaat") or "").lower()
    permit_start_dt = permit.get("einddatum")
    # permit_end_dt = permit.get("datuM_TOT")

    if "verleend" not in result or not permit_start_dt:
        return False
    return permit_start_dt <= reference_dt


def has_valid_bed_and_breakfast_permit(vergunningen, reference_dt=None):
    serializer = PowerbrowserSerializer(data=vergunningen, many=True)
    serializer.is_valid(raise_exception=True)
    return any(
        is_valid_bed_and_breakfast_permit(permit, reference_dt=reference_dt)
        for permit in serializer.validated_data
    )


def get_is_bed_and_breakfast_for_bag_id(bag_id, reference_dt=None):
    vergunningen = PowerbrowserRequest().get_vergunningen_with_bag_id(bag_id)
    return has_valid_bed_and_breakfast_permit(
        vergunningen,
        reference_dt=reference_dt,
    )


class PowerbrowserRequest:
    def __init__(self):
        self.base_url = settings.POWERBROWSER_BASE_URL
        self.api_key = settings.POWERBROWSER_API_KEY

    def get_vergunningen_with_bag_id(self, bag_id):
        bearer_token = self._get_powerbrowser_bearer_token()
        vergunningen = self._get_powerbrowser_vergunningen(bearer_token, bag_id)
        self._logout_from_powerbrowser(bearer_token)
        return vergunningen

    def _get_powerbrowser_bearer_token(self):
        json = {"apiKey": self.api_key}
        url = os.path.join(self.base_url, "token")
        response = self._perform_api_call(url, json=json)
        bearer_token = response.text
        return bearer_token

    def _perform_api_call(self, url, json=None, bearer_token=None, method="post"):
        headers = {"Authorization": f"Bearer {bearer_token}"} if bearer_token else {}
        response = getattr(requests, method)(
            url=url,
            json=json,
            headers=headers,
            timeout=(2, 5),
        )
        logger.info(f"Called url {response.url} with method {method.upper()}")
        response.raise_for_status()
        return response

    def _logout_from_powerbrowser(self, bearer_token):
        url = os.path.join(self.base_url, "token")
        self._perform_api_call(url, bearer_token=bearer_token, method="delete")

    def _get_powerbrowser_vergunningen(self, bearer_token, bag_id):
        json = {
            "reportFileName": "D:\\Genetics\\PowerForms\\Overzichten\\Wonen\\Zakentop.gov",
            "parameters": [
                {
                    "name": "BAG_ID",
                    "type": "string",
                    "value": {"stringValue": f"{bag_id}"},
                }
            ],
        }
        url = os.path.join(self.base_url, "report/runsavedreport")
        response = self._perform_api_call(url, json=json, bearer_token=bearer_token)
        return response.json()


def _contains_bed_and_breakfast_marker(permit):
    return (permit.get("product") or "").lower() == BED_AND_BREAKFAST_PRODUCT
