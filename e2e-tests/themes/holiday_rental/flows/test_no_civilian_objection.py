import unittest

from api.client import Client
from api.config import SummonTypes, Themes, Violation, api_config
from api.mock import get_case_mock
from api.tasks import (
    CheckNotices,
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    FeedbackReporters,
    MonitorIncomingView,
    ProcessNotice,
    ScheduleVisit,
    Visit,
)
from api.validators import ValidateOpenTasks


class TestNoCivilianObjection(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            FeedbackReporters(),  # BUG in Spiff. According to Nicoline if Violation=True, we should Feedback the reporters
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            ValidateOpenTasks([MonitorIncomingView]),
            # Cannot test because of timer!
            # WaitForTimer(MonitorIncomingView(objection=False)),
            # MonitorIncomingView(objection=False),
            # CheckIncomingView(objection=Objection.NO),
            # AssertNumberOfOpenTasks(0),
        ]

        case.run_steps(steps)
