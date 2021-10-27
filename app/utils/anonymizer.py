import logging
import random

from apps.addresses.models import Address
from apps.cases.models import Case, CaseClose, CaseState, CitizenReport
from apps.debriefings.models import Debriefing
from apps.decisions.models import Decision
from apps.schedules.models import Schedule
from apps.summons.models import Summon, SummonedPerson
from apps.visits.models import Visit
from django.conf import settings
from faker import Faker

logger = logging.getLogger(__name__)

ANONYMIZER_ENV_BLACKLIST = ("production",)


class Anonymizer:
    fields_for_models_conf = []

    def __init__(self, _fields_for_models_conf):
        if settings.ENVIRONMENT in ANONYMIZER_ENV_BLACKLIST:
            raise Exception(
                f"Wrong enviroment: The env {settings.ENVIRONMENT} does not allow anonyzation"
            )
        self.fields_for_models_conf = _fields_for_models_conf

    def perform_update(self):
        for f in self.fields_for_models_conf:
            objs = [
                f[0](
                    **{
                        **{"id": id},
                        **f[1],
                    }
                )
                for id in f[0].objects.values_list("id", flat=True)
            ]

            logger.info(f"Anonymize '{f[0].__name__}' instances")
            try:
                f[0].objects.bulk_update(objs, list(f[1].keys()))
            except Exception as e:
                logger.error(f"ERROR: {f[0].__name__} {str(e)}")

        logger.info("Anonymization done")


def get_default_anonymizer():
    fake = Faker()
    postal_codes = range(1000, 1109)
    conf = [
        (Case, {"description": fake.paragraph(nb_sentences=2)}),
        (
            Address,
            {
                "bag_id": "0363010012143319",
                "street_name": fake.street_name(),
                "number": fake.building_number(),
                "suffix_letter": "",
                "suffix": "",
                "postal_code": f"{str(random.choice(postal_codes))}{fake.bothify(text='??').upper()}",
                "lat": 52.36801669236072,
                "lng": 4.899564069922884,
            },
        ),
        (CaseState, {"information": fake.sentence(nb_words=2)}),
        (
            CaseClose,
            {
                "description": fake.paragraph(nb_sentences=2),
            },
        ),
        (
            CitizenReport,
            {
                "reporter_name": fake.name(),
                "reporter_phone": fake.phone_number(),
                "reporter_email": fake.ascii_email(),
                "description_citizenreport": fake.paragraph(nb_sentences=2),
                "advertisement_linklist": [],
            },
        ),
        (
            Debriefing,
            {
                "violation_result": {},
                "feedback": fake.paragraph(nb_sentences=2),
            },
        ),
        (
            Decision,
            {
                "sanction_amount": 100,
                "description": fake.paragraph(nb_sentences=2),
            },
        ),
        (
            Schedule,
            {
                "description": fake.paragraph(nb_sentences=2),
            },
        ),
        (
            Summon,
            {
                "description": fake.paragraph(nb_sentences=2),
            },
        ),
        (
            SummonedPerson,
            {
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "preposition": "",
            },
        ),
        (
            Visit,
            {
                "can_next_visit_go_ahead_description": fake.paragraph(nb_sentences=2),
                "suggest_next_visit_description": fake.paragraph(nb_sentences=2),
                "notes": fake.paragraph(nb_sentences=2),
            },
        ),
    ]

    return Anonymizer(conf)
