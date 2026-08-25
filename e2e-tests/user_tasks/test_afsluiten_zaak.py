from api.config import NextStep
from api.tasks.close_case import (
    test_close_case,
    test_close_case_concept,
    test_uitzetten_vervolgstap,
)
from api.tasks.visit import test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateNoOpenTasks, ValidateOpenTasks
from dateutil import parser


def get_due_date(test, case):
    task = test.client.get_case_tasks(case.data["id"])[0]
    return parser.parse(task["due_date"])


class TestAfsluitenZaak(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *test_uitzetten_vervolgstap.get_steps(next_step=NextStep.CLOSE),
        )
        ValidateOpenTasks(test_close_case_concept)

    def test_sluiten(self):
        self.get_case().run_steps(
            *test_uitzetten_vervolgstap.get_steps(next_step=NextStep.CLOSE),
            test_close_case(),
        )
        ValidateNoOpenTasks()

    def test_hercontrole(self):
        self.get_case().run_steps(
            *test_uitzetten_vervolgstap.get_steps(next_step=NextStep.RECHECK),
        )
        ValidateOpenTasks(test_inplannen_status)
