from api.config import Subject
from api.tasks.close_case import test_afsluiten_zaak
from api.test import DefaultAPITest
from api.validators import Validator


class ValidateSubjects(Validator):
    def __init__(self, subjects):
        subjects.sort()
        self.subjects = subjects

    def run(self, client, case):
        case_subjects = case.data["subjects"]
        case_subjects.sort()
        if case_subjects != self.subjects:
            raise Exception(
                f"Case's ({case}) subject ({case_subjects}) are not as excpected ({self.subjects})"
            )


class TestSubjects(DefaultAPITest):
    def get_case_data(self):
        return {
            "subjects": [
                Subject.HolidayRental.GEEN_NACHTVERBLIJF,
            ]
        }

    def test(self):
        case = self.get_case()

        # Validate if create-case added the right subjects
        case.run_steps(
            ValidateSubjects([Subject.HolidayRental.GEEN_NACHTVERBLIJF]),
        )

        # Change the subjects
        updated_subjects = [
            Subject.HolidayRental.GEEN_NACHTVERBLIJF,
            Subject.HolidayRental.ONTBREKEN_INSCHRIJVING_BRP,
        ]

        self.client.call(
            "put",
            f"/cases/{case.data['id']}/",
            {
                "address": case.data["address"],
                "theme": case.data["theme"],
                "reason": case.data["reason"],
                "subjects": updated_subjects,
            },
        )

        # Update case's data
        new_subjects = list(
            map(
                lambda subject: subject["id"],
                self.client.call("get", f"/cases/{case.data['id']}/")["subjects"],
            )
        )
        case.data["subjects"] = new_subjects

        # Check if the subjects are updated and keep their value after close case
        case.run_steps(
            ValidateSubjects(updated_subjects),
            *test_afsluiten_zaak.get_steps(),
            ValidateSubjects(updated_subjects),
        )

        # Validate timeline only on create-case event
        # events = self.client.get_case_events(case.data["id"])
