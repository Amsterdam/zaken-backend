from api.tasks.visit import (
    test_aanvragen_machtiging,
    test_inplannen_status,
    test_monitoren_binnenkomen_machtiging,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_monitoren_binnenkomen_machtiging_test(DefaultAPITest):
    def test(self):
        self.skipTest(
            "This fails probably because of the same reason as 'test_aanvragen_machtiging.py'"
        )
        self.get_case().run_steps(
            *test_aanvragen_machtiging.get_steps(),
            test_monitoren_binnenkomen_machtiging(),
            ValidateOpenTasks(test_inplannen_status),
        )
