from api.config import Violation
from api.tasks.debrief import (
    test_opstellen_beeldverslag,
    test_opstellen_rapport_van_bevindingen,
    test_terugkoppelen_melder_2,
    test_verwerken_debrief,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_opstellen_beeldverslag_test(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *test_verwerken_debrief.get_steps(violation=Violation.YES),
            ValidateOpenTasks(
                test_opstellen_beeldverslag,
                test_opstellen_rapport_van_bevindingen,
            ),
            test_opstellen_beeldverslag(),
            ValidateOpenTasks(test_opstellen_rapport_van_bevindingen),
        )
