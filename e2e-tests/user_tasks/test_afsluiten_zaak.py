from api.config import DecisionType, NextStep
from api.tasks.close_case import test_afsluiten_zaak, test_uitzetten_vervolgstap
from api.tasks.decision import (
    test_versturen_invordering_belastingen,
    test_verwerken_definitieve_besluit,
)
from api.tasks.renounce_decision import (
    test_nakijken_afzien_voornemen,
    test_opstellen_concept_voornemen_afzien,
    test_verwerken_definitieve_voornemen_afzien,
)
from api.tasks.visit import test_inplannen_status
from api.test import DefaultAPITest
from api.util import midnight
from api.validators import ValidateOpenTasks
from dateutil import parser
from dateutil.relativedelta import relativedelta


def get_due_date(test, case):
    task = test.client.get_case_tasks(case.data["id"])[0]
    return parser.parse(task["due_date"])


class TestAfsluitenZaak(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *test_uitzetten_vervolgstap.get_steps(next_step=NextStep.CLOSE),
        )
        ValidateOpenTasks(test_afsluiten_zaak)

    def test_hercontrole(self):
        self.get_case().run_steps(
            *test_uitzetten_vervolgstap.get_steps(next_step=NextStep.RECHECK),
        )
        ValidateOpenTasks(test_inplannen_status)

    def test_due_date_with_non_renounced(self):
        case = self.get_case()
        case.run_steps(
            *test_verwerken_definitieve_besluit.get_steps(
                type=DecisionType.Vakantieverhuur.PREVENTIVE_BURDEN
            ),
            test_uitzetten_vervolgstap(),
        )
        due_date = get_due_date(self, case).timestamp()
        expected = (midnight() + relativedelta(months=13)).timestamp()
        self.assertEqual(expected, due_date)

    def test_due_date_with_only_renouned(self):
        case = self.get_case()
        case.run_steps(
            *test_verwerken_definitieve_besluit.get_steps(
                type=DecisionType.Vakantieverhuur.NO_DECISION
            ),
            test_opstellen_concept_voornemen_afzien(),
            test_nakijken_afzien_voornemen(),
            test_verwerken_definitieve_voornemen_afzien(),
            test_uitzetten_vervolgstap(),
        )
        due_date = get_due_date(self, case)
        expected = midnight() + relativedelta(weeks=1)
        # print(f"midnight: {midnight()}, expected: {expected}, due_date: {due_date}")
        self.assertEqual(expected.timestamp(), due_date.timestamp())
