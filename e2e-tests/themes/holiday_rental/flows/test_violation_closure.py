from api.config import ReviewRequest, SummonTypes, Violation
from api.tasks.closing_procedure import (
    ContactOwner,
    JudgeReopeningRequest,
    MonitorReopeningRequest,
    MonitorReopeningRequestToBeDelivered,
    Reopen,
    SaveFireBrigadeAdvice,
    ScheduleRecheck,
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
        self.skipTest(
            "#BUG After ProcessNotice, case has PlanNextStep instead of SaveFireBrigadeAdvice and MonitorReopeningRequest. @xavier is going to add closing_procedure to director."
        )
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
            WaitForTimer(),
            ContactOwner(),
            JudgeReopeningRequest(review_request=ReviewRequest.DECLINED),
            MonitorReopeningRequestToBeDelivered(),
            JudgeReopeningRequest(),
            Reopen(),
            ScheduleRecheck(),
            ValidateOpenTasks(ScheduleVisit),
        )
