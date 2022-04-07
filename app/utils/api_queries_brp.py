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

    if settings.ENVIRONMENT == "production":
        return get_mock_brp()

    url = f"{settings.BRP_API_URL}"

    response = requests.get(
        url,
        params=queryParams,
        timeout=30,
        headers={
            "Authorization": request.headers.get("Authorization"),
        },
    )
    response.raise_for_status()

    results = [
        {
            "geboortedatum": p.get("geboorte", {}).get("datum", {}).get("datum"),
            "geslachtsaanduiding": p.get("geslachtsaanduiding", ""),
            "geslachtsnaam": p.get("naam", {}).get("geslachtsnaam"),
            "voorletters": p.get("naam", {}).get("voorletters"),
            "voornamen": p.get("naam", {}).get("voornamen"),
            "voorvoegsel_geslachtsnaam": p.get("naam", {}).get("voorvoegsel"),
            "datum_begin_relatie_verblijfadres": p.get("verblijfplaats", {})
            .get("datumAanvangAdreshouding", {})
            .get("datum"),
            "ingeschrevenpersoon_raw": p,
        }
        for p in response.json().get("_embedded", {}).get("ingeschrevenpersonen", [])
    ]
    return response.json()
    return {
        "message": "real data",
        "results": results,
    }


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
