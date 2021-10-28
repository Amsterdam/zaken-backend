from api.config import ReviewRequest, SummonTypes, Violation
from api.tasks.close_case import PlanNextStep
from api.tasks.closing_procedure import (
    ContactOwner,
    JudgeReopeningRequest,
    MonitorReopeningRequest,
    MonitorReopeningRequestToBeDelivered,
    Reopen,
    SaveFireBrigadeAdvice,
)
from api.tasks.debrief import (
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
)
from api.tasks.summon import CheckNotices, ProcessNotice
from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestViolationClosure(DefaultAPITest):
    def test(self):
        self.skipTest("PlanNextStep is not given")
        self.get_case().run_steps(
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            ValidateOpenTasks(CheckNotices),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.CLOSURE),
            ValidateOpenTasks(
                SaveFireBrigadeAdvice,
                MonitorReopeningRequest,
            ),
            SaveFireBrigadeAdvice(),
            WaitForTimer(),
            ContactOwner(),
            JudgeReopeningRequest(review_request=ReviewRequest.DECLINED),
            MonitorReopeningRequestToBeDelivered(),
            JudgeReopeningRequest(),
            Reopen(),
            PlanNextStep(),
            ValidateOpenTasks(ScheduleVisit),
        )
