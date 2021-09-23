import unittest

from api.client import Client
from api.config import ReviewRequest, SummonTypes, Themes, api_config
from api.mock import get_case_mock
from api.tasks import (
    AssertNumberOfOpenTasks,
    CheckNotices,
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    FeedbackReporters,
    JudgeReopeningRequest,
    MonitorReopeningRequest,
    MonitorReopeningRequestToBeDelivered,
    Reopen,
    SaveFireBrigadeAdvice,
    ScheduleRecheck,
    ScheduleVisit,
    Summon,
    Visit,
)


class TestViolationClosure(unittest.TestCase):
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
            Summon(type=SummonTypes.HolidayRental.CLOSURE),
            AssertNumberOfOpenTasks(2),
            SaveFireBrigadeAdvice(),
            MonitorReopeningRequest(),
            JudgeReopeningRequest(review_request=ReviewRequest.DECLINED),
            MonitorReopeningRequestToBeDelivered(),
            JudgeReopeningRequest(),
            Reopen(),
            ScheduleRecheck(),
            AssertNumberOfOpenTasks(0),
        )

        case.run_steps(steps)
