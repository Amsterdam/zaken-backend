import logging
import random
from string import Template

from apps.addresses.models import Address
from apps.camunda.models import GenericCompletedTask as CamundaGenericCompletedTask
from apps.cases.models import Case, CaseClose, CaseState, CitizenReport
from apps.debriefings.models import Debriefing
from apps.decisions.models import Decision
from apps.schedules.models import Schedule
from apps.summons.models import Summon, SummonedPerson
from apps.visits.models import Visit
from apps.workflow.models import GenericCompletedTask
from django.conf import settings
from faker import Faker

logger = logging.getLogger(__name__)

ANONYMIZER_ENV_BLACKLIST = ("production",)


default_addresses = (
    {
        "bag_id": "0363200012145295",
        "street_name": "Amstel",
        "number": 1,
        "suffix_letter": "",
        "suffix": "",
        "postal_code": "1011PN",
        "lat": 52.36801669236072,
        "lng": 4.899564069922884,
    },
    {
        "bag_id": "0363200000480137",
        "street_name": "Osdorpplein",
        "number": 1000,
        "suffix_letter": "",
        "suffix": "",
        "postal_code": "1068TG",
        "lat": 52.35778032597312,
        "lng": 4.806664109665068,
    },
    {
        "bag_id": "0363200000476521",
        "street_name": "Buikslotermeerplein",
        "number": 2000,
        "suffix_letter": "",
        "suffix": "",
        "postal_code": "1025XL",
        "lat": 52.40083489421504,
        "lng": 4.932922359792739,
    },
    {
        "bag_id": "0363200012061665",
        "street_name": "Oranje-Vrijstaatplein",
        "number": 2,
        "suffix_letter": "",
        "suffix": "",
        "postal_code": "1093NG",
        "lat": 52.356747356447634,
        "lng": 4.930896390575606,
    },
    {
        "bag_id": "0363200000504751",
        "street_name": "Bos en Lommerplein",
        "number": 250,
        "suffix_letter": "",
        "suffix": "",
        "postal_code": "1055EK",
        "lat": 52.378005455254204,
        "lng": 4.84514175935018,
    },
    {
        "bag_id": "0363200012085071",
        "street_name": "President Kennedylaan",
        "number": 923,
        "suffix_letter": "",
        "suffix": "",
        "postal_code": "1079MZ",
        "lat": 52.34047764231988,
        "lng": 4.893953309353364,
    },
    {
        "bag_id": "0363200000512588",
        "street_name": "Anton de Komplein",
        "number": 150,
        "suffix_letter": "",
        "suffix": "",
        "postal_code": "1102CW",
        "lat": 52.31624077472882,
        "lng": 4.956475409945793,
    },
)


class Anonymizer:
    fields_for_models_conf = []

    def __init__(self, _fields_for_models_conf):
        if settings.ENVIRONMENT in ANONYMIZER_ENV_BLACKLIST:
            raise Exception(
                f"Wrong enviroment: The env {settings.ENVIRONMENT} does not allow anonyzation"
            )
        self.fields_for_models_conf = _fields_for_models_conf

    def perform_update(self):
        logger.info("Creating default addresses")
        address_data = [
            Address(**address)
            for address in default_addresses
            if not Address.objects.filter(
                bag_id=address.get("bag_id", ""),
            )
        ]
        Address.objects.bulk_create(address_data)

        existing_default_addresses = Address.objects.filter(
            bag_id__in=[a.get("bag_id") for a in default_addresses]
        )

        logger.info("Update all cases with a random default address")
        random_cases_addresses = [
            Case(
                **{
                    "id": case.id,
                    "address": random.choice(existing_default_addresses),
                }
            )
            for case in Case.objects.all()
        ]

        Case.objects.bulk_update(
            random_cases_addresses,
            [
                "address",
            ],
        )

        logger.info("Delete all other addresses")

        Address.objects.all().exclude(
            id__in=existing_default_addresses.values_list("id", flat=True)
        ).delete()

        def parse_field_value(value, data):
            if isinstance(value, str):
                return Template(value).safe_substitute(data)
            elif callable(value):
                return value()
            return value

        for f in self.fields_for_models_conf:
            logger.info(f"Creating anonymizions for '{f[0].__name__}' instances")
            objs = [
                f[0](
                    **{
                        **{"id": id},
                        **dict(
                            (k, parse_field_value(v, {"id": id}))
                            for k, v in f[1].items()
                        ),
                    }
                )
                for id in f[0].objects.values_list("id", flat=True)
            ]
            logger.info(f"Updating '{f[0].__name__}' instances")
            try:
                f[0].objects.bulk_update(objs, list(f[1].keys()))
            except Exception as e:
                logger.error(f"ERROR: {f[0].__name__} {str(e)}")

        logger.info("Anonymization done")


def get_street_name():
    fake = Faker()
    return fake.street_name()


def get_building_number():
    fake = Faker()
    return fake.building_number()


def get_postal_code():
    fake = Faker()
    postal_codes = range(1000, 1109)
    return f"{str(random.choice(postal_codes))}{fake.bothify(text='??').upper()}"


def get_phone_number():
    fake = Faker()
    return fake.phone_number()


def get_sentence():
    fake = Faker()
    return fake.sentence(nb_words=2)


def get_paragraph():
    fake = Faker()
    return fake.paragraph(nb_sentences=2)


def get_name():
    fake = Faker()
    return fake.name()


def get_first_name():
    fake = Faker()
    return fake.first_name()


def get_last_name():
    fake = Faker()
    return fake.last_name()


def get_email():
    fake = Faker()
    return fake.ascii_email()


def get_default_anonymizer():
    conf = [
        (
            CamundaGenericCompletedTask,
            {
                "variables": {},
            },
        ),
        (
            Case,
            {
                "description": get_paragraph,
            },
        ),
        (
            CaseState,
            {
                "information": get_sentence,
            },
        ),
        (
            CaseClose,
            {
                "description": get_paragraph,
            },
        ),
        (
            CitizenReport,
            {
                "reporter_name": get_name,
                "reporter_phone": get_phone_number,
                "reporter_email": get_email,
                "description_citizenreport": get_paragraph,
                "advertisement_linklist": [],
            },
        ),
        (
            Debriefing,
            {
                "violation_result": {},
                "feedback": get_paragraph,
            },
        ),
        (
            Decision,
            {
                "sanction_amount": 100,
                "description": get_paragraph,
            },
        ),
        (
            Schedule,
            {
                "description": get_paragraph,
            },
        ),
        (
            Summon,
            {
                "description": get_paragraph,
            },
        ),
        (
            SummonedPerson,
            {
                "first_name": get_first_name,
                "last_name": get_last_name,
                "preposition": "",
            },
        ),
        (
            Visit,
            {
                "can_next_visit_go_ahead_description": get_paragraph,
                "suggest_next_visit_description": get_paragraph,
                "notes": get_paragraph,
            },
        ),
        (
            GenericCompletedTask,
            {
                "variables": {},
            },
        ),
    ]

    return Anonymizer(conf)
