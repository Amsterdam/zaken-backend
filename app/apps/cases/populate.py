import random
import uuid

from apps.cases.const import MOCK_BAG_IDS, PROJECTS
from apps.cases.models import Address, Case, Project
from faker import Faker


def delete_all():
    Case.objects.all().delete()
    Address.objects.all().delete()
    Project.objects.all().delete()


def create_projects():
    projects = [Project.get(project) for project in PROJECTS]
    return projects


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


def create_cases(projects, addresses):
    cases = []
    for i in range(10):
        project = random.choice(projects)
        address = random.choice(addresses)
        identification = uuid.uuid4()
        case = Case.objects.create(
            project=project, address=address, identification=identification
        )
        cases.append(case)

    return cases
