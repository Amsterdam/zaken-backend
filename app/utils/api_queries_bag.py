import logging

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt

logger = logging.getLogger(__name__)

headers = {"x-api-key": settings.BAG_API_PUBLIC_KEY}


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def do_bag_search_benkagg_by_id(identificatie):
    """
    Search BAG by identificatie (nummeraanduiding_id).
    With benkagg you cannot search by bag_id (adresseerbaarobject_id).
    You can use the parameters 'verblijfsobjectIdentificatie', 'ligplaatsIdentificatie' or 'standplaatsIdentificatie'
    with a bag_id but then you need to know the type of object first (woonhuis, woonboot of woonwagen).
    This is really annoying.
    """
    address_search = requests.get(
        settings.BAG_API_BENKAGG_SEARCH_URL,
        params={"identificatie": identificatie},
        headers=headers,
        timeout=30,
    )
    return address_search.json()


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def do_bag_search_pdok_by_bag_id(bag_id):
    """
    Search BAG PDOK using a 'adresseerbaarobject_id'
    """
    address_search = requests.get(
        settings.BAG_API_PDOK_URL,
        params={
            "q": bag_id,
            "fq": f"gemeentenaam:(amsterdam) AND (type:adres) AND (adresseerbaarobject_id: {bag_id}) AND (adrestype: hoofdadres)",
        },
        timeout=5,
    )

    return address_search.json()
