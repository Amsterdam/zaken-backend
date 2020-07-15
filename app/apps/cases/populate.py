import random
import uuid

from apps.cases.const import MOCK_BAG_IDS, PROJECTS
from apps.cases.models import Address, Case, CaseType
from faker import Faker


def delete_all():
    Case.objects.all().delete()
    Address.objects.all().delete()
    CaseType.objects.all().delete()


def create_case_types():
    case_types = [CaseType.get(case_type) for case_type in PROJECTS]
    return case_types


def create_addresses():
    fake = Faker("nl_NL")
    addresses = []
    for i in range(10):
        address = Address.objects.create(
            bag_id=fake.bban(),
            street_name=fake.street_name(),
            number=fake.building_number(),
            postal_code=fake.postcode(),
        )
        addresses.append(address)

    return addresses


def create_cases(case_types, addresses):
    cases = []
    for i in range(10):
        case_type = random.choice(case_types)
        address = random.choice(addresses)
        identification = uuid.uuid4()
        case = Case.objects.create(
            case_type=case_type, address=address, identification=identification
        )
        cases.append(case)

    return cases
