import logging

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt

logger = logging.getLogger(__name__)


def get_brp_by_bag_id(request, bag_id):
    """Returns BRP data by bag_"""

    queryParams = {
        "verblijfplaats__nummeraanduidingIdentificatie": f"{bag_id}",
    }
    return get_brp(request, queryParams)


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
def get_brp(request, queryParams):
    """Returns BRP data"""

    url = f"{settings.BRP_API_URL}"

    response = requests.get(
        url,
        params=queryParams,
        timeout=30,
        headers={
            "Authorization": request.headers.get("Authorization"),
        },
    )

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
