import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_energie_label(bag_id):
    response = requests.get(
        settings.PUNTENTELLER_ENERGIELABEL_API_URL,
        params={"bagVerblijfsobjectId": bag_id},
        timeout=10,
    )
    response.raise_for_status()
    response_data = response.json()
    resultaten = response_data.get("_embedded", {}).get("energielabel", [])
    if not resultaten:
        return None

    laatste_resultaat = max(
        resultaten,
        key=lambda item: (
            item.get("registratiedatum") or "",
            item.get("opnamedatum") or "",
        ),
    )
    return {
        "energielabel": laatste_resultaat.get("energieklasse"),
        "bouwjaar": laatste_resultaat.get("bouwjaar"),
    }


def get_woz(nummeraanduiding_id):
    response = requests.get(
        f"{settings.PUNTENTELLER_WOZ_API_URL}{nummeraanduiding_id}",
        timeout=10,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    response_data = response.json()
    waarden = response_data.get("wozWaarden", [])
    woz_object = response_data.get("wozObject", {})
    if not waarden:
        return {
            "woz": None,
            "woz_jaar": None,
            "wozobjectnummer": woz_object.get("wozobjectnummer"),
        }

    laatste_waarde = max(waarden, key=lambda item: item.get("peildatum") or "")
    peildatum = laatste_waarde.get("peildatum")
    return {
        "woz": laatste_waarde.get("vastgesteldeWaarde"),
        "woz_jaar": int(peildatum.split("-")[0]) if peildatum else None,
        "wozobjectnummer": woz_object.get("wozobjectnummer"),
    }


def get_oppervlakte(adresseerbaarobject_id):
    response = requests.get(
        settings.PUNTENTELLER_VERBLIJFSOBJECT_API_URL,
        params={"identificatie": adresseerbaarobject_id},
        timeout=10,
    )
    response.raise_for_status()
    response_data = response.json()
    verblijfsobjecten = response_data.get("_embedded", {}).get("verblijfsobjecten", [])
    if not verblijfsobjecten:
        return None

    laatste_verblijfsobject = max(
        verblijfsobjecten,
        key=lambda item: (item.get("volgnummer") or 0, item.get("plusvolgnummer") or 0),
    )
    return laatste_verblijfsobject.get("oppervlakte")
