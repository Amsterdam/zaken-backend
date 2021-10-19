import unittest

from api.client import Client
from api.config import Themes, Violation, api_config
from api.mock import get_case_mock
from api.tasks import Debrief, FeedbackReporters, HomeVisitReport, Visit
from api.validators import AssertOpenTasks


class TestSendToOtherTeam(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            *Visit.get_steps(),
            Debrief(violation=Violation.SEND_TO_OTHER_THEME),
            AssertOpenTasks(
                [
                    FeedbackReporters,  # BUG: We should feedback the reporters after sending to another team. (actually a new feature request)
                    HomeVisitReport,
                ]
            ),
        ]

        case.run_steps(steps)
