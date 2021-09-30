import unittest

from api.client import Client
from api.config import Themes, Violation, api_config
from api.mock import get_case_mock
from api.tasks import AssertNextOpenTasks, Debrief, ScheduleVisit, Task, Visit


class TestSendToOtherTeam(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.SEND_TO_OTHER_THEME),
            AssertNextOpenTasks(
                [
                    Task.feedback_reporters
                    if self.api.legacy_mode
                    else None,  # BUG in Spiff
                    Task.create_home_visit_report,
                ]
            ),
        ]

        case.run_steps(steps)
