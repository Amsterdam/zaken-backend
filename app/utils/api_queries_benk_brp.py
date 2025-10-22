import logging
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

        # Extract all BSNs from the first API response
        personen = ingeschreven_personen.get("personen", [])
        burgerservicenummers = [
            p.get("burgerservicenummer")
            for p in personen
            if p.get("burgerservicenummer")
        ]

        if not burgerservicenummers:
            logger.warning("No BSNs found in BRP response")
            return ingeschreven_personen

        # Perform a second API call using all BSNs
        personen_met_bsn = self._fetch_personen_met_bsn(
            access_token, burgerservicenummers, user_email
        )

        # Combine both API responses into one result object
        combined_result = {
            "personen": personen_met_bsn.get("personen", []),
            "operation_ids": [
                ingeschreven_personen.get("operation_id"),
                personen_met_bsn.get("operation_id"),
            ],
        }

        return combined_result

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
            "X-Correlation-ID": operation_id,
            "X-Task-Description": "Wonen",
            "X-User": user_email,
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        response = getattr(requests, method)(
            url=url,
            json=json,
            headers=headers,
            timeout=(3, 10),
        )
        response.raise_for_status()

        # Add operation_id to response for logging/tracing purposes
        response.operation_id = operation_id
        return response

    def _fetch_ingeschreven_personen(
        self, access_token, nummeraanduiding_id, user_email
    ):
        # First API call: fetch all registered persons for a given address ID
        payload = {
            "type": "ZoekMetNummeraanduidingIdentificatie",
            "nummeraanduidingIdentificatie": f"{nummeraanduiding_id}",
            "inclusiefOverledenPersonen": "true",
        }
        url = f"{self.base_url.rstrip('/')}/personen"
        response = self._perform_api_call(
            url, json=payload, access_token=access_token, user_email=user_email
        )
        data = response.json()
        data["operation_id"] = response.operation_id
        return data

    def _fetch_personen_met_bsn(self, access_token, burgerservicenummers, user_email):
        # Second API call: fetch detailed person data using an array of BSNs
        payload = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": burgerservicenummers,
        }
        url = f"{self.base_url.rstrip('/')}/personen"
        response = self._perform_api_call(
            url, json=payload, access_token=access_token, user_email=user_email
        )
        data = response.json()
        data["operation_id"] = response.operation_id
        return data
