import random
import uuid
from datetime import date

from apps.cases.const import BAG_IDS, PROJECTS, STADIA
from apps.cases.models import Address, Case, CaseType, OpenZaakState, OpenZaakStateType
from faker import Faker


def delete_all():
    OpenZaakState.objects.all().delete()
    OpenZaakStateType.objects.all().delete()
    Case.objects.all().delete()
    Address.objects.all().delete()
    CaseType.objects.all().delete()


def create_states(cases, state_types):
    states = []
    for case in cases:
        for i in range(5):
            state_type = random.choice(state_types)

            if i == 4:
                end_date = None
            else:
                end_date = date.today()

            state = OpenZaakState.objects.create(
                state_type=state_type,
                case=case,
                start_date=date.today(),
                end_date=end_date,
                gauge_date=date.today(),
            )
            states.append(state)

    return states


def create_state_types():
    state_types = [OpenZaakStateType.get(state_type) for state_type in STADIA]
    return state_types


def create_case_types():
    case_types = [CaseType.get(case_type) for case_type in PROJECTS]
    return case_types


def create_addresses():
    # fake = Faker("nl_NL")
    addresses = []
    for bag_id in BAG_IDS:
        address = Address.objects.create(bag_id=bag_id)
        addresses.append(address)
    # for i in range(10):
    #     address = Address.objects.create(
    #         bag_id=fake.bban(),
    #         street_name=fake.street_name(),
    #         number=fake.building_number(),
    #         postal_code=fake.postcode(),
    #     )
    #     addresses.append(address)

    return addresses


def create_cases(case_types, addresses):
    cases = []
    for i in range(10):
        case_type = random.choice(case_types)
        address = random.choice(addresses)
        identification = uuid.uuid4()
        case = Case.objects.create(
            case_type=case_type,
            address=address,
            identification=identification,
            start_date=date.today(),
        )
        cases.append(case)

    return cases
