import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


ENERGIELABEL_FIELDS = (
    "energieklasse,bouwjaar,energieindex,registratiedatum,opnamedatum,metingGeldigTot"
)

VERBLIJFSOBJECT_FIELDS = "oppervlakte,volgnummer,plusvolgnummer"


def get_energie_label(bag_id):
    response = requests.get(
        settings.PUNTENTELLER_ENERGIELABEL_API_URL,
        params={
            "bagVerblijfsobjectId": bag_id,
            "_fields": ENERGIELABEL_FIELDS,
        },
        timeout=30,
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
        "energieindex": laatste_resultaat.get("energieindex"),
        "registratiedatum": laatste_resultaat.get("registratiedatum"),
        "opnamedatum": laatste_resultaat.get("opnamedatum"),
        "meting_geldig_tot": laatste_resultaat.get("metingGeldigTot"),
    }


def get_woz(nummeraanduiding_id):
    response = requests.get(
        f"{settings.PUNTENTELLER_WOZ_API_URL}{nummeraanduiding_id}",
        timeout=10,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()

    response_data = response.json()

    woz_object = response_data.get("wozObject", {})
    woz_waarden = response_data.get("wozWaarden", [])

    return {
        "woz_waarden": [
            {
                "peildatum": waarde["peildatum"],
                "vastgestelde_waarde": waarde["vastgesteldeWaarde"],
            }
            for waarde in woz_waarden
        ]
        or None,
        "wozobjectnummer": woz_object.get("wozobjectnummer"),
    }


def get_oppervlakte(adresseerbaarobject_id):
    response = requests.get(
        settings.PUNTENTELLER_VERBLIJFSOBJECT_API_URL,
        params={
            "identificatie": adresseerbaarobject_id,
            "_fields": VERBLIJFSOBJECT_FIELDS,
        },
        timeout=30,
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
