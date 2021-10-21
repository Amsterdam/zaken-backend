from api.config import DecisionType, ObjectionValid, SummonTypes, Violation
from api.tasks.debrief import (
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
)
from api.tasks.decision import (
    CheckConceptDecision,
    CreateConceptDecision,
    Decision,
    JudgeView,
    SendTaxCollection,
)
from api.tasks.summon import CheckNotices, MonitorIncomingView, ProcessNotice
from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.validators import ValidateNoOpenTasks


class TestInvalidCivilianObjection(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            MonitorIncomingView(),
            JudgeView(objection_valid=ObjectionValid.NO),
            CreateConceptDecision(),
            CheckConceptDecision(),
            Decision(type=DecisionType.HolidayRental.FINE),
            SendTaxCollection(),
            ValidateNoOpenTasks(),
        )
