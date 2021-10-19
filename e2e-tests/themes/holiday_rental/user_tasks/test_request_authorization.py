from api.config import Violation
from api.tasks.debrief import (
    Debrief,
    MonitorIncomingAuthorization,
    RequestAuthorization,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestRequestAuthorization(DefaultAPITest):
    def test(self):
        self.case.run_steps(
            *Debrief.get_steps(violation=Violation.ADDITIONAL_VISIT_WITH_AUTHORIZATION),
            RequestAuthorization(),
            ValidateOpenTasks(MonitorIncomingAuthorization),
        )
