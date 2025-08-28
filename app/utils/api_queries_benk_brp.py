import logging
import os
import uuid

import requests
from django.conf import settings
from opentelemetry import trace

logger = logging.getLogger(__name__)


class BrpRequest:
    def __init__(self):
        self.base_url = settings.BENK_BRP_API_URL

    def get_brp_with_nummeraanduiding_id(self, nummeraanduiding_id, user_email):
        access_token = self._get_access_token()
        ingeschreven_personen = self._fetch_ingeschreven_personen(
            access_token, nummeraanduiding_id, user_email
        )
        return ingeschreven_personen

    def _get_access_token(self):
        url = settings.OIDC_OP_TOKEN_ENDPOINT
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": settings.BENK_BRP_CLIENT_ID,
            "scope": settings.BENK_BRP_SCOPE,
            "client_secret": settings.BENK_BRP_CLIENT_SECRET,
            "grant_type": "client_credentials",
        }

        response = requests.post(url, headers=headers, data=data, timeout=(2, 5))
        response.raise_for_status()

        return response.json().get("access_token")

    def _perform_api_call(
        self, url, method="post", json=None, access_token=None, user_email=None
    ):
        # Obtain current trace id from OpenTelemetry, fallback to new UUID if missing
        current_span = trace.get_current_span()
        span_context = current_span.get_span_context() if current_span else None
        trace_id_int = (
            span_context.trace_id if span_context and span_context.trace_id else 0
        )
        operation_id = f"{trace_id_int:032x}" if trace_id_int else uuid.uuid4().hex
        headers = {
            "Authorization": f"Bearer {access_token}" if access_token else "",
            "X-Correlation-ID": operation_id,
            "X-Task-Description": "Wonen",
            "X-User": user_email,
        }

        response = getattr(requests, method)(
            url=url,
            json=json,
            headers=headers,
            timeout=(3, 10),
        )
        response.raise_for_status()
        return response

    def _fetch_ingeschreven_personen(
        self, access_token, nummeraanduiding_id, user_email
    ):
        payload = {
            "type": "ZoekMetNummeraanduidingIdentificatie",
            "nummeraanduidingIdentificatie": f"{nummeraanduiding_id}",
            "inclusiefOverledenPersonen": "true",
        }
        url = os.path.join(self.base_url, "personen")
        response = self._perform_api_call(
            url, json=payload, access_token=access_token, user_email=user_email
        )
        return response.json()
