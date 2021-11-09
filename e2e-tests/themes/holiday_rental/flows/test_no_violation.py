from api.config import Violation
from api.tasks.debrief import Debrief, HomeVisitReport, InformReporterNoViolation
from api.tasks.director import FeedbackReporters
from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.validators import ValidateNoOpenTasks


class TestNoViolation(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.NO),
            InformReporterNoViolation(),
            FeedbackReporters(),
            HomeVisitReport(),
            # TODO Current/old implementation gave PlanNextStep, but even
            #   better would be skipping this step all together.
            # PlanNextStep(),
            # Close(),
            ValidateNoOpenTasks(),
        )
