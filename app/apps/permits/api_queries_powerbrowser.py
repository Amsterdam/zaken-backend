import logging
import os

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


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
