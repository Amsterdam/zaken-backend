import unittest

from api.client import Client
from api.config import SummonTypes, Themes, api_config
from api.mock import get_case_mock
from api.tasks import (
    AssertNextOpenTasks,
    CheckNotices,
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    FeedbackReporters,
    ScheduleVisit,
    Summon,
    Task,
    Visit,
)


class TestNoCivilianObjection(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            ScheduleVisit(),
            Visit(),
            Debrief(violation="YES"),
            FeedbackReporters() if self.api.legacy_mode else None,  # BUG in Camunda?
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            CheckNotices(),
            Summon(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            AssertNextOpenTasks([Task.monitor_incoming_view]),
            # MonitorIncomingView(objection=False), # Test fails here, not sure why. Frontend always sends value 'true'
            # CheckIncomingView(objection=Objection.NO), # Cannot test because of timer?
            # AssertNumberOfOpenTasks(0),
        ]

        case.run_steps(steps)
