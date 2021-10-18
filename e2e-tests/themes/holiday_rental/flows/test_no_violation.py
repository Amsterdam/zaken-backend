import unittest

from api.client import Client
from api.config import Themes, Violation, api_config
from api.mock import get_case_mock
from api.tasks import (
    Close,
    Debrief,
    FeedbackReporters,
    HomeVisitReport,
    PlanNextStep,
    ScheduleVisit,
    Visit,
)
from api.validators import ValidateNumberOfOpenTasks


class TestNoViolation(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.NO),
            FeedbackReporters(),  # BUG: If Violation=No (or send to other team) we also expect FeedbackReporters (actually feature request)
            HomeVisitReport(),  # BUG: Gives Timeline issue
            # BUG: no more steps available
            PlanNextStep(),  # Current/old implementation gave PlanNextStep, but even better would be skipping this step all together.
            Close(),
        ]

        steps.append(ValidateNumberOfOpenTasks(0))

        case.run_steps(steps)
