from api.config import Reason, Themes
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


def get_case_mock(
    theme_id=Themes.HOLIDAY_RENTAL,
    reason=Reason.NOTIFICATION,
    address=Address,
    subjects=[],
    description_citizenreport=None,
    identification=None,
):
    return {
        "theme": theme_id,
        "reason": reason,
        "address": address,
        "subjects": subjects,
        "description_citizenreport": description_citizenreport,
        "identification": identification,
    }
