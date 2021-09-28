import unittest

from api.client import Client
from api.config import Themes, api_config
from api.mock import get_case_mock
from api.tasks import (
    AssertNumberOfOpenTasks,
    Close,
    Debrief,
    FeedbackReporters,
    HomeVisitReport,
    PlanNextStep,
    ScheduleVisit,
    Visit,
)


class TestNoViolation(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = (
            ScheduleVisit(),
            Visit(),
            AssertNumberOfOpenTasks(1),
            Debrief(),  # no violation
            AssertNumberOfOpenTasks(2 if self.api.legacy_mode else 1),  # BUG in Spiff
            FeedbackReporters() if self.api.legacy_mode else None,  # BUG in Spiff
            HomeVisitReport(),
            PlanNextStep(),
            Close(),
            AssertNumberOfOpenTasks(0),
        )

        case.run_steps(steps)
