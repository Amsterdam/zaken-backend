from api.config import (
    NextStep,
    ReopenRequest,
    ReviewReopenRequest,
    SummonTypes,
    Violation,
)
from api.tasks.close_case import PlanNextStep
from api.tasks.closing_procedure import (
    ContactOwnerFirst,
    ContactOwnerSecond,
    JudgeReopeningRequest,
    MonitorReopeningRequest,
    MonitorReopeningRequestToBeDelivered,
    ReturnKey,
    SaveFireBrigadeAdvice,
    SaveReopenRequest,
)
from api.tasks.debrief import (
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    InformReporter,
)
from api.tasks.summon import CheckNotices, ProcessNotice
from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestViolationClosure(DefaultAPITest):
    def test_direct(self):
        self.get_case().run_steps(
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            InformReporter(),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            ValidateOpenTasks(CheckNotices),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.CLOSURE),
            SaveFireBrigadeAdvice(),
            MonitorReopeningRequest(),
            JudgeReopeningRequest(review_request=ReviewReopenRequest.DECLINED),
            MonitorReopeningRequestToBeDelivered(),
            JudgeReopeningRequest(),
            SaveReopenRequest(),
            ReturnKey(),
            PlanNextStep(next_step=NextStep.RECHECK),
            ValidateOpenTasks(ScheduleVisit),
        )

    def test_timer(self):
        self.get_case().run_steps(
            *SaveFireBrigadeAdvice.get_steps(),
            WaitForTimer(),
            ContactOwnerFirst(),
            ValidateOpenTasks(JudgeReopeningRequest),
        )

    def test_timer_second(self):
        self.get_case().run_steps(
            *SaveFireBrigadeAdvice.get_steps(),
            MonitorReopeningRequest(),
            JudgeReopeningRequest(review_request=ReviewReopenRequest.DECLINED),
            WaitForTimer(),
            ContactOwnerSecond(),
            ValidateOpenTasks(MonitorReopeningRequestToBeDelivered),
        )
