import logging

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt

logger = logging.getLogger(__name__)

# The following fields were presented in the example spreadsheet documentation, which should mirror the BRP API:
# (TODO: remove this once the BRP API is up and its documentation is accessible )
# A-nummer
# BSN
# sleutel paraplu
# Onderzoek algemeen
# Burgerlijke staat
# Geboortedatum
# Geboortelandcode
# Geslachtsaanduiding
# Geslachtsnaam
# Voorletters
# Voornamen
# Voorvoegsel geslachtsnaam
# Indicatie geheim
# Landcode immigratie
# Datum inschrijving
# Gemeente code inschrijving
# Aanduiding naamgebruik
# Datum begin relatie verblijfadres
# Aanduiding in onderzoek verblijfadres
# Straatnaam
# Huisnummer
# Huisletter 0=n.v.t.
# Huisnummertoevoeging 0=n.v.t.
# Postcode


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def get_brp_by_bag_id(bag_id):
    """ Returns BRP data"""
    # TODO: Replace with actual request when BRP API is ready
    """
    curl -H "MKS_APPLICATIE: fp_burger" -H "MKS_GEBRUIKER: test_burger"  -H "Authorization: Bearer ACCESS_TOKEN" "https://acc.api.secure.amsterdam.nl/gob_stuf/brp/ingeschrevenpersonen?verblijfplaats__postcode=1098WE&verblijfplaats__huisnummer=208&expand=partners,ouders,kinderen"

    """
    return get_mock_brp()


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def get_brp_by_address(address, request):
    """ Returns BRP data"""

    url = f"{settings.BRP_API_URL}"
    queryParams = {
        "verblijfplaats__postcode": address.postal_code,
        "verblijfplaats__straat": address.street_name,
        "verblijfplaats__huisnummer": address.number,
        "verblijfplaats__huisnummertoevoeging": address.suffix,
        "verblijfplaats__huisletter": address.suffix_letter,
    }
    print(queryParams)
    print(request.headers.get("Authorization"))
    print(url)

    response = requests.get(
        url,
        params=queryParams,
        timeout=30,
        headers={
            "MKS_APPLICATIE": "fp_burger",
            "MKS_GEBRUIKER": "test_burger",
            "Authorization": request.headers.get("Authorization"),
        },
    )
    response.raise_for_status()
    print(response)
    print(response.text)
    print(response.url)
    print(response.headers)
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
        }
        for p in response.json().get("_embedded", {}).get("ingeschrevenpersonen", [])
    ]
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
