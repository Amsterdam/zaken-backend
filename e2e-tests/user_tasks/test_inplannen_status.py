from api.tasks.visit import (
    test_bepalen_processtap_standaard,
    test_doorgeven_status_top,
    test_inplannen_status,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_inplannen_status_test(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            test_bepalen_processtap_standaard(),
            test_inplannen_status(),
            ValidateOpenTasks(test_doorgeven_status_top),
        )
