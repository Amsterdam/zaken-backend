import logging

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt

logger = logging.getLogger(__name__)


def get_vakantieverhuur_meldingen(bag_id, query_params, use_retry=True):
    """
    Get the Vakantieverhuur meldingen from the Toeristische Verhuur register
    """

    def _get_vakantieverhuur_meldingen_internal():
        header = {
            "x-api-key": settings.VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_ACCESS_TOKEN
        }
        url = (
            f"{settings.VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_URL}meldingen/{bag_id}"
        )

        response = requests.get(
            url=url,
            params=query_params,
            headers=header,
            timeout=30,
        )

        response.raise_for_status()

        return response.json(), response.status_code

    if use_retry:
        _get_vakantieverhuur_meldingen_internal = retry(
            stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR)
        )(_get_vakantieverhuur_meldingen_internal)

    return _get_vakantieverhuur_meldingen_internal()


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def get_vakantieverhuur_registration(registration_number):
    """
    Get the Vakantieverhuur registration
    """
    header = {"x-api-key": settings.VAKANTIEVERHUUR_REGISTRATIE_API_ACCESS_TOKEN}
    url = (
        f"{settings.VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_URL}{registration_number}"
    )

    response = requests.get(
        url=url,
        headers=header,
        verify="/usr/local/share/ca-certificates/adp_rootca.crt",
    )
    response.raise_for_status()

    return response.json()


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def get_bsn_vakantieverhuur_registrations(bsn_number):
    """
    Get the Vakantieverhuur registrations using a BSN number
    """
    header = {"x-api-key": settings.VAKANTIEVERHUUR_REGISTRATIE_API_ACCESS_TOKEN}
    url = f"{settings.VAKANTIEVERHUUR_REGISTRATIE_API_URL}bsn/{bsn_number}"

    response = requests.get(
        url=url,
        headers=header,
        verify="/usr/local/share/ca-certificates/adp_rootca.crt",
    )
    response.raise_for_status()

    return response.json()


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def get_bag_vakantieverhuur_registrations(bag_id):
    """
    Get the Vakantieverhuur registrations using a BSN number
    """
    header = {"x-api-key": settings.VAKANTIEVERHUUR_REGISTRATIE_API_ACCESS_TOKEN}
    url = f"{settings.VAKANTIEVERHUUR_REGISTRATIE_API_URL}bagid/{bag_id}"

    response = requests.get(
        url=url,
        headers=header,
        verify="/usr/local/share/ca-certificates/adp_rootca.crt",
    )
    response.raise_for_status()

    return response.json()
