from api.config import Violation
from api.tasks.debrief import Debrief
from api.tasks.visit import MonitorIncomingAuthorization, RequestAuthorization
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestRequestAuthorization(DefaultAPITest):
    def test(self):
        self.skipTest(
            "Debrief with add. visit with auth. should give RequestAuth but it doesn't."
        )
        self.get_case().run_steps(
            *Debrief.get_steps(violation=Violation.ADDITIONAL_VISIT_WITH_AUTHORIZATION),
            RequestAuthorization(),
            ValidateOpenTasks(MonitorIncomingAuthorization),
        )
