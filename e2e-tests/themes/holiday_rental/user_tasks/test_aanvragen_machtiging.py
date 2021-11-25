from api.config import Violation
from api.tasks.debrief import test_verwerken_debrief
from api.tasks.visit import (
    test_aanvragen_machtiging,
    test_monitoren_binnenkomen_machtiging,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_aanvragen_machtiging_test(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *test_verwerken_debrief.get_steps(
                violation=Violation.ADDITIONAL_VISIT_WITH_AUTHORIZATION
            ),
            test_aanvragen_machtiging(),
            ValidateOpenTasks(test_monitoren_binnenkomen_machtiging),
        )
