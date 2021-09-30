import unittest

from api.client import Client
from api.config import ReviewRequest, SummonTypes, Themes, api_config
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
    JudgeReopeningRequest,
    MonitorReopeningRequest,
    MonitorReopeningRequestToBeDelivered,
    Reopen,
    SaveFireBrigadeAdvice,
    ScheduleRecheck,
    ScheduleVisit,
    Summon,
    Task,
    Visit,
)


class TestViolationClosure(unittest.TestCase):
    def setUp(self):
        self.api = Client(api_config)

    def test(self):
        case = self.api.create_case(get_case_mock(Themes.HOLIDAY_RENTAL))
        steps = [
            ScheduleVisit(),
            Visit(),
            Debrief(violation="YES"),
            FeedbackReporters() if self.api.legacy_mode else None,  # Bug in Camunda?
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            AssertNumberOfOpenTasks(1),
            CheckNotices(),
            Summon(type=SummonTypes.HolidayRental.CLOSURE),
        ]
        if self.api.legacy_mode:  # BUG in Spiff
            steps.extend(
                [
                    AssertNextOpenTasks(
                        [
                            Task.save_fire_brigade_advice,
                            Task.monitor_reopening_request,
                        ]
                    ),
                    SaveFireBrigadeAdvice(),
                    MonitorReopeningRequest(),
                    JudgeReopeningRequest(review_request=ReviewRequest.DECLINED),
                    MonitorReopeningRequestToBeDelivered(),
                    JudgeReopeningRequest(),
                    Reopen(),
                    ScheduleRecheck(),
                ]
            )

        steps.append(AssertNumberOfOpenTasks(0))

        case.run_steps(steps)
