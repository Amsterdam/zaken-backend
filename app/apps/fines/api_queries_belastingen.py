import logging

import requests
from django.conf import settings
from faker import Faker
from tenacity import after_log, retry, stop_after_attempt

logger = logging.getLogger(__name__)


def get_fines(id, use_retry=True):
    """
    Search the Belasting API for fines with case_id identification
    """

    def _get_fines_internal():
        parameter = {"identificatienummer": id}
        header = {"authorization": f"Bearer {settings.BELASTING_API_ACCESS_TOKEN}"}

        response = requests.get(
            url=settings.BELASTING_API_URL,
            headers=header,
            params=parameter,
            verify="/usr/local/share/ca-certificates/adp_rootca.crt",
            timeout=6,
        )
        response.raise_for_status()

        return response.json()

    if use_retry:
        _get_fines_internal = retry(
            stop=stop_after_attempt(3), after=after_log(logger, logging.ERROR)
        )(_get_fines_internal)

    return _get_fines_internal()


def get_mock_fines(case_id):
    fake = Faker("nl_NL")
    return {
        "message": "mocked data",
        "items": [
            {
                "identificatienummer": case_id,
                "vorderingnummer": fake.ssn(),
                "jaar": 2020,
                "soort_vordering": "PBN",
                "omschrijving_soort_vordering": "Publiekrechtelijk (niet-fiscaal)",
                "indicatie_publiekrechtelijk": "N",
                "subjectnr": fake.ssn(),
                "opgemaaktenaam": fake.name(),
                "subjectnr_opdrachtgever": fake.ssn(),
                "opgemaaktenaam_opdrachtgever": "Wonen inc. vord.",
                "runnr": fake.ssn(),
                "omschrijving_run": "Wonen inc. vord.",
                "code_runwijze": "IVO",
                "omschrijving_runwijze": "Incidentele vorderingen",
                "dagtekening": "2020-01-29T23:00:00Z",
                "vervaldatum": "2020-02-28T23:00:00Z",
                "indicatie_combi_dwangbevel": "N",
                "notatekst": None,
                "omschrijving": None,
                "invorderingstatus": "AANM",
                "indicatie_bet_hern_bevel": "N",
                "landcode": None,
                "kenteken": None,
                "bonnummer": None,
                "bedrag_opgelegd": 10000,
                "bedrag_open_post_incl_rente": 10215.50,
                "totaalbedrag_open_kosten": 15,
                "bedrag_open_rente": 200.50,
                "reden_opschorting": None,
                "omschrijving_1": f"Het onttrekken van de woonruimte {fake.address()}",
                "omschrijving_2": "aan de woonruimtevoorraad zonder dat hiervoor",
            }
        ],
    }
