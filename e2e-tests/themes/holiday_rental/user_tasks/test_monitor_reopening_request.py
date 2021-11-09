from api.tasks.closing_procedure import (
    ContactOwnerFirst,
    JudgeReopeningRequest,
    MonitorReopeningRequest,
    SaveFireBrigadeAdvice,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestMonitorReopeningRequest(DefaultAPITest):
    def test_no_reopen(self):
        self.get_case().run_steps(
            *SaveFireBrigadeAdvice.get_steps(),
            MonitorReopeningRequest(),
            ValidateOpenTasks(JudgeReopeningRequest),
        )

    def test_reopen(self):
        self.get_case().run_steps(
            *SaveFireBrigadeAdvice.get_steps(),
            WaitForTimer(),
            ValidateOpenTasks(ContactOwnerFirst),
        )
