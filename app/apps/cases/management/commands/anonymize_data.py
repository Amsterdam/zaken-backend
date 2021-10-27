import logging

from apps.addresses.models import Address
from apps.cases.models import Case
from django.core.management.base import BaseCommand
from faker import Faker

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        fake = Faker()

        range(1000, 1109)
        cases = Case.objects.all()
        Address.objects.all()
        fake_addresses = [
            {
                "street_name": fake.street_name(),
                "number": fake.building_number(),
                "city": fake.city(),
                # "postal_code": f"{str(random.choice(postal_codes))}{fake.bothify(text="####??").upper()}",
            }
        ]
        print(fake_addresses)

        logger.info(len(cases))
