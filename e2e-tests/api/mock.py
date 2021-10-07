from api.config import Reason
from faker import Faker

fake = Faker()
profile = fake.profile(fields=["username", "mail", "name"])


def get_person():
    return {
        "id": fake.uuid4(),
        "email": profile["mail"],
        "username": profile["username"],
        "first_name": profile["name"].split(" ")[0],
        "last_name": " ".join(profile["name"].split(" ")[1:]),
        "full_name": profile["name"],
    }


Address = {"bag_id": "234"}


def get_case_mock(theme_id):
    return {
        "theme": theme_id,
        "reason": Reason.NOTIFICATION,
        "address": Address,
    }
