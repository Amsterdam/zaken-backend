import logging

import requests
from django.conf import settings
from tenacity import after_log, retry, stop_after_attempt

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def do_bag_search_id(bag_id):
    """
    Search BAG using a BWV 'landelijk BAG ID'
    """
    address_search = requests.get(
        settings.BAG_API_SEARCH_URL, params={"q": bag_id}, timeout=0.5
    )
    return address_search.json()


@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR))
def get_address_bag_data(address_uri):
    """
    Does a BAG Query given a URI
    """
    address_bag_data = requests.get(address_uri, timeout=0.5)
    return address_bag_data.json()
