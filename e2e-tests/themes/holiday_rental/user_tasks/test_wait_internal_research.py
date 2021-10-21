from api.config import Violation
from api.tasks.debrief import Debrief, WaitInternalResearch
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestWaitInternalResearch(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *Debrief.get_steps(violation=Violation.ADDITIONAL_RESEARCH_REQUIRED),
            WaitInternalResearch(),
            ValidateOpenTasks(Debrief),
        )
