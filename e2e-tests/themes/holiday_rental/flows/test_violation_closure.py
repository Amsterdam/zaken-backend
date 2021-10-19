from api.config import SummonTypes, Violation
from api.tasks.closing_procedure import MonitorReopeningRequest, SaveFireBrigadeAdvice
from api.tasks.debrief import (
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
)
from api.tasks.summon import CheckNotices, ProcessNotice
from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestViolationClosure(DefaultAPITest):
    def test(self):
        self.skipTest(
            "#BUG After ProcessNotice, case has PlanNextStep instead of SaveFireBrigadeAdvice and MonitorReopeningRequest"
        )
        self.case.run_steps(
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            ValidateOpenTasks(CheckNotices),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.CLOSURE),
            # BUG  Spiff gives PlanNextStep !!!
            ValidateOpenTasks(
                SaveFireBrigadeAdvice,
                MonitorReopeningRequest,
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
        )
