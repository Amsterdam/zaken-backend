from api.tasks.closing_procedure import (
    ContactOwner,
    MonitorReopeningRequest,
    SaveFireBrigadeAdvice,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateNoOpenTasks, ValidateOpenTasks


class TestMonitorReopeningRequest(DefaultAPITest):
    def test(self):
        self.skipTest("Closing procedure is not started properly after ProcessNotice.")
        self.get_case().run_steps(
            *SaveFireBrigadeAdvice.get_steps(),
            MonitorReopeningRequest(),
            ValidateNoOpenTasks(),
            WaitForTimer(),
            ValidateOpenTasks(ContactOwner),
        )
