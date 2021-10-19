import unittest

from api.client import Client
from api.config import Themes, api_config
from api.events import CaseEvent, CitizenReportEvent
from api.mock import get_case_mock
from api.tasks import ScheduleVisit
from api.validators import AssertEvents, AssertNumberOfOpenTasks


class TestTimeline(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test_citizenreport_and_sia(self):
        case = self.api.create_case(
            dict(
                **get_case_mock(Themes.HOLIDAY_RENTAL),
                **{
                    "description_citizenreport": "This is a report.",
                    # "identification": "123" # als deze ook nodig dan vermelden in CitizenReportEvent doc.
                }
            )
        )
        steps = [
            ScheduleVisit(),
            AssertEvents(
                [
                    CaseEvent,
                    CitizenReportEvent,
                ]
            ),
        ]

        steps.append(AssertNumberOfOpenTasks(0))

        case.run_steps(steps)
