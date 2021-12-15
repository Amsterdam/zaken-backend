from api.config import Violation
from api.tasks.debrief import test_afwachten_intern_onderzoek, test_verwerken_debrief
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_afwachten_intern_onderzoek_test(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *test_verwerken_debrief.get_steps(
                violation=Violation.ADDITIONAL_RESEARCH_REQUIRED
            ),
            test_afwachten_intern_onderzoek(),
            ValidateOpenTasks(test_verwerken_debrief),
        )
