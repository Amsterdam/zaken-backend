import logging
import uuid

import requests
from django.conf import settings
from opentelemetry import trace

logger = logging.getLogger(__name__)


class BrpRequest:
    def __init__(self):
        self.base_url = settings.BENK_BRP_API_URL
        self.session = requests.Session()
        # Common headers reused for all requests
        self.session.headers.update({"Content-Type": "application/json"})

    def _get_operation_id(self):
        """Return the current OpenTelemetry trace ID, or generate a new UUID if not available."""
        current_span = trace.get_current_span()
        span_context = current_span.get_span_context() if current_span else None
        trace_id_int = (
            span_context.trace_id if span_context and span_context.trace_id else 0
        )
        return f"{trace_id_int:032x}" if trace_id_int else uuid.uuid4().hex

    def get_brp_with_nummeraanduiding_id(self, nummeraanduiding_id, user_email):
        """Fetch persons from BRP based on address ID, optionally followed by BSN lookup."""
        access_token = self._get_access_token()
        operation_id = self._get_operation_id()

        # First API call: fetch registered persons by address
        ingeschreven_personen = self._fetch_ingeschreven_personen(
            access_token, nummeraanduiding_id, user_email, operation_id
        )

        personen = ingeschreven_personen.get("personen", [])
        burgerservicenummers = [
            p.get("burgerservicenummer")
            for p in personen
            if p.get("burgerservicenummer")
        ]

        # No BSNs found, return early
        if not burgerservicenummers:
            logger.warning("No BSNs found in BRP response")
            return {
                "personen": personen,
                "operation_id": operation_id,
            }

        # Second API call: fetch detailed person data by BSN
        personen_met_bsn = self._fetch_personen_met_bsn(
            access_token, burgerservicenummers, user_email, operation_id
        )

        return {
            "personen": personen_met_bsn.get("personen", []),
            "operation_id": operation_id,
        }

    def _get_access_token(self):
        """Retrieve an OAuth2 access token using client credentials."""
        url = settings.OIDC_OP_TOKEN_ENDPOINT
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": settings.BENK_BRP_CLIENT_ID,
            "scope": settings.BENK_BRP_SCOPE,
            "client_secret": settings.BENK_BRP_CLIENT_SECRET,
            "grant_type": "client_credentials",
        }

        response = self.session.post(url, headers=headers, data=data, timeout=(2, 5))
        response.raise_for_status()
        return response.json().get("access_token")

    def _perform_api_call(
        self,
        url,
        method="post",
        json=None,
        access_token=None,
        user_email=None,
        operation_id=None,
    ):
        """Perform an HTTP call to the BRP API with tracing and authentication headers."""
        operation_id = operation_id or self._get_operation_id()

        headers = {
            "X-Correlation-ID": operation_id,
            "X-Task-Description": "Wonen",
            "X-User": user_email,
        }

        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                headers=headers,
                timeout=(3, 10),
            )

        except Exception as e:
            logger.error(
                f"BRP request failed "
                f"url={url} "
                f"operation_id={operation_id} "
                f"error={e}"
            )
            raise

        if not response.ok:
            logger.error(
                f"BRP returned error "
                f"status={response.status_code} "
                f"url={url} "
                f"operation_id={operation_id} "
                f"body={response.text}"
            )

        try:
            response.raise_for_status()
        except Exception:
            raise

        response.operation_id = operation_id
        return response

    def _fetch_ingeschreven_personen(
        self, access_token, nummeraanduiding_id, user_email, operation_id
    ):
        """Fetch all registered persons for a given address ID."""
        payload = {
            "type": "ZoekMetNummeraanduidingIdentificatie",
            "nummeraanduidingIdentificatie": f"{nummeraanduiding_id}",
            "inclusiefOverledenPersonen": True,
        }
        url = f"{self.base_url.rstrip('/')}/personen"
        response = self._perform_api_call(
            url,
            json=payload,
            access_token=access_token,
            user_email=user_email,
            operation_id=operation_id,
        )
        return response.json()

    def _fetch_personen_met_bsn(
        self, access_token, burgerservicenummers, user_email, operation_id
    ):
        """Fetch detailed person data for a list of BSNs."""
        payload = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": burgerservicenummers,
        }
        url = f"{self.base_url.rstrip('/')}/personen"
        response = self._perform_api_call(
            url,
            json=payload,
            access_token=access_token,
            user_email=user_email,
            operation_id=operation_id,
        )
        return response.json()
