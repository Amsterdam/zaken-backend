import unittest

from api.client import Client
from api.config import SummonTypes, Themes, api_config
from api.mock import get_case_mock
from api.tasks import (
    AssertNextOpenTasks,
    AssertNumberOfOpenTasks,
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


class TestViolationWarningLetter(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = (
            ScheduleVisit(),
            Visit(),
            Debrief(violation="YES"),
            AssertNumberOfOpenTasks(4),
            FeedbackReporters(),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            AssertNumberOfOpenTasks(1),
            CheckNotices(),
            Summon(type=SummonTypes.HolidayRental.LEGALIZATION_LETTER),
            AssertNextOpenTasks([Task.monitor_incoming_permit_request]),
        )

        case.run_steps(steps)
