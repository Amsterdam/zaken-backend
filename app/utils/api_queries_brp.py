import logging

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
def get_brp(bag_id):
    """ Returns BRP data"""
    # TODO: Replace with actual request when BRP API is ready
    return get_mock_brp()


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
                "datum_begin_relatie_verblijadres": "1992-05-26T23:00:00Z",  # Note: This was marked as in spreadsheet in the following format: 19920526,
            }
        ],
    }
