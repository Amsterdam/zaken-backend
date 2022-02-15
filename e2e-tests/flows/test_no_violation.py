from api.config import Violation
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.debrief import (
    test_opstellen_verkorte_rapportage_huisbezoek,
    test_terugkoppelen_melder_1,
    test_verwerken_debrief,
)
from api.tasks.visit import test_doorgeven_status_top, test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestNoViolation(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            test_inplannen_status(),
            test_doorgeven_status_top(),
            test_verwerken_debrief(violation=Violation.NO),
            test_opstellen_verkorte_rapportage_huisbezoek(),
            ValidateOpenTasks(test_uitzetten_vervolgstap),
        )
