from api.config import NextStep, ReviewRequest, SummonTypes, Violation
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
    def test_direct(self):
        self.skipTest("PlanNextStep is not given. Xavier is working on it")
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
            MonitorReopeningRequest(),
            JudgeReopeningRequest(review_request=ReviewRequest.DECLINED),
            MonitorReopeningRequestToBeDelivered(),
            JudgeReopeningRequest(),
            Reopen(),
            PlanNextStep(next_step=NextStep.RECHECK),
            ValidateOpenTasks(ScheduleVisit),
        )

    def test_timer(self):
        self.get_case().run_steps(
            *SaveFireBrigadeAdvice.get_steps(),
            WaitForTimer(),
            ContactOwner(),
            ValidateOpenTasks(JudgeReopeningRequest),
        )
