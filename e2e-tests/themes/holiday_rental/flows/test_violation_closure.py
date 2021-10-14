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
    JudgeReopeningRequest,
    MonitorReopeningRequest,
    MonitorReopeningRequestToBeDelivered,
    ProcessNotice,
    Reopen,
    SaveFireBrigadeAdvice,
    ScheduleRecheck,
    ScheduleVisit,
    Visit,
)
from api.validators import AssertNumberOfOpenTasks, AssertOpenTasks


class TestViolationClosure(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            AssertNumberOfOpenTasks(1),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.CLOSURE),
            # BUG  Spiff gives PlanNextStep !!!
            AssertOpenTasks(
                [
                    SaveFireBrigadeAdvice,
                    MonitorReopeningRequest,
                ]
            ),
            SaveFireBrigadeAdvice(),
            # We need to implement timers first to be able to test this flow
            # MonitorReopeningRequest(),
            # WaitForTimer(),
            # JudgeReopeningRequest(review_request=ReviewRequest.DECLINED),
            # MonitorReopeningRequestToBeDelivered(),
            # JudgeReopeningRequest(),
            # Reopen(),
            # ScheduleRecheck(),
            # AssertNumberOfOpenTasks(0),
        ]

        case.run_steps(steps)
