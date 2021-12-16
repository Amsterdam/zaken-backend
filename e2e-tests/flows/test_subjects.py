from api.config import Reason, Subject, Theme, VisitNextStep
from api.tasks.close_case import test_afsluiten_zaak
from api.tasks.visit import test_bepalen_processtap
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
            "theme_id": Theme.ONDERMIJNING,
            "reason": Reason.Ondermijning.EIGEN_ONDERZOEK,
            "subjects": [
                Subject.Ondermijning.HENNEP,
            ],
        }

    def test(self):
        case = self.get_case()

        # Validate if create-case added the right subjects
        case.run_steps(
            ValidateSubjects([Subject.Ondermijning.HENNEP]),
        )

        # Change the subjects
        updated_subject_ids = [
            Subject.Ondermijning.HENNEP,
            Subject.Ondermijning.CRIMINEEL_GEBRUIK,
        ]

        self.client.call(
            "patch",
            f"/cases/{case.data['id']}/",
            {
                "subject_ids": updated_subject_ids,
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
            ValidateSubjects(updated_subject_ids),
            test_bepalen_processtap(
                visit_next_step=VisitNextStep.VISIT_WITHOUT_AUTHORIZATION
            ),
            *test_afsluiten_zaak.get_steps(),
            ValidateSubjects(updated_subject_ids),
        )

        # Validate timeline only on create-case event
        # events = self.client.get_case_events(case.data["id"])
