from api.tasks.visit import (
    MonitorIncomingAuthorization,
    RequestAuthorization,
    ScheduleVisit,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestMonitorIncomingAuthorization(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *RequestAuthorization.get_steps(),
            MonitorIncomingAuthorization(),
            ValidateOpenTasks(ScheduleVisit),
        )
