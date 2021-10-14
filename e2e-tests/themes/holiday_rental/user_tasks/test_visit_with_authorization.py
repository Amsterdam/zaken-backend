import unittest

from api.client import Client
from api.config import Situations, Themes, Violation, api_config
from api.mock import get_case_mock
from api.tasks import (
    Debrief,
    MonitorIncomingAuthorization,
    RequestAuthorization,
    ScheduleVisit,
    Visit,
)
from api.validators import AssertOpenTasks


class TestInvalidCivilianObjection(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test_access_granted(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))

        steps = [
            *ScheduleVisit.get_steps(),
            Visit(situation=Situations.NO_COOPERATION, can_next_visit_go_ahead=False),
            Debrief(violation=Violation.ADDITIONAL_VISIT_WITH_AUTHORIZATION),
            RequestAuthorization(),
            AssertOpenTasks([MonitorIncomingAuthorization]),
        ]

        case.run_steps(steps)
