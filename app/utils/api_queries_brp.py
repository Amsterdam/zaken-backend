import logging

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt
from utils.exceptions import MKSPermissionsError

logger = logging.getLogger(__name__)


def get_brp_by_nummeraanduiding_id(request, nummeraanduiding_id, brp_access_token):
    """Returns BRP data by bag_"""

    queryParams = {
        "verblijfplaats__identificatiecodenummeraanduiding": f"{nummeraanduiding_id}",
        "inclusiefoverledenpersonen": "true",
        "expand": "partners,ouders,kinderen",
    }
    return get_brp(request, queryParams, brp_access_token)


def get_brp_by_address(request, postal_code, number, suffix, suffix_letter):
    """Returns BRP data by address info"""

    queryParams = {
        "verblijfplaats__postcode": postal_code,
        "verblijfplaats__huisnummer": number,
        "inclusiefoverledenpersonen": "true",
        "expand": "partners,ouders,kinderen",
    }
    if suffix_letter:
        queryParams.update(
            {
                "verblijfplaats__huisletter": suffix_letter,
            }
        )
    if suffix:
        queryParams.update(
            {
                "verblijfplaats__huisnummertoevoeging": suffix,
            }
        )
    return get_brp(request, queryParams)


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def get_brp(request, queryParams, brp_access_token):
    """Returns BRP data"""

    url = f"{settings.BRP_API_URL}"

    response = requests.get(
        url,
        params=queryParams,
        timeout=30,
        headers={
            "Authorization": f"Bearer {brp_access_token}",
        },
    )
    if response.status_code == 403:
        raise MKSPermissionsError()

    return response.json(), response.status_code


def get_mock_brp():
    return {
        "message": "mocked data",
        "results": [
            {
                "geboortedatum": "1955-05-23T23:00:00Z",  # Note: This was marked as in spreadsheet in the following format: 19550523,
                "geslachtsaanduiding": "V",
                "geslachtsnaam": "Gouderinge",
                "voorletters": "AC",
                "voornamen": "Anne Carmen",
                "voorvoegsel_geslachtsnaam": "van",
                "datum_begin_relatie_verblijfadres": "1992-05-26T23:00:00Z",  # Note: This was marked as in spreadsheet in the following format: 19920526,
            }
        ],
    }
