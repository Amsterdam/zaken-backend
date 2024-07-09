import logging

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt

logger = logging.getLogger(__name__)

headers = {"x-api-key": settings.BAG_API_PUBLIC_KEY}


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def do_bag_search_benkagg_by_bag_id(bag_id, is_boat=False):
    """
    Search BAG identificatie (nummeraanduiding_id) and stadsdeel using an adresseertVerblijfsobjectId
    """
    identification_type = "adresseertVerblijfsobjectIdentificatie"
    if is_boat:
        identification_type = "ligplaatsIdentificatie"

    address_search = requests.get(
        settings.BAG_API_BENKAGG_SEARCH_URL,
        params={identification_type: bag_id},
        headers=headers,
        timeout=30,
    )
    return address_search.json()


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def do_bag_search_by_bag_id(bag_id):
    """
    Search BAG using a BWV 'landelijk BAG ID'
    """
    address_search = requests.get(
        settings.BAG_API_SEARCH_URL,
        params={
            "q": bag_id,
            "fq": f"gemeentenaam:(amsterdam) AND (type:adres) AND (adresseerbaarobject_id: {bag_id}) AND (adrestype: hoofdadres)",
        },
        timeout=5,
    )

    return address_search.json()


# BWV migration queries
def get_bag_search_query(address):
    """
    Constructs a BAG search query using the address data
    """
    hsltr = address.get("huisletter", "") or ""
    toev = address.get("toev", "") or ""

    query = f"{address.get('postcode')} {address.get('huisnummer')} {hsltr}{toev}"

    return query.strip()


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def do_bag_search_address(address):
    """
    Search BAG using a BWV address
    """
    query = get_bag_search_query(address)
    address_search = requests.get(
        settings.BAG_API_SEARCH_URL,
        params={"q": query},
        timeout=30,
    )
    return address_search.json()


def do_bag_search_address_exact(address):
    """
    Filter BAG results using bag address search with exact matching on query string fields
    """
    result = do_bag_search_address(address)

    result["results"] = [
        r
        for r in result["results"]
        if r.get("huisnummer") == address.get("huisnummer", "")
        and r.get("postcode") == address.get("postcode", "")
        and r.get("bag_huisletter") == (address.get("huisletter", "") or "")
        and r.get("bag_toevoeging") == str(address.get("toev", "") or "")
    ]
    result["count_hits"] = len(result["results"])
    result["count"] = len(result["results"])
    return result
