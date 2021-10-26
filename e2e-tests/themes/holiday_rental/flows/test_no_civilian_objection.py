from api.config import Objection, SummonTypes, Violation
from api.tasks.debrief import (
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
)
from api.tasks.decision import CreateConceptDecision
from api.tasks.director import FeedbackReporters
from api.tasks.summon import (
    CheckIncomingView,
    CheckNotices,
    MonitorIncomingView,
    ProcessNotice,
)
from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestNoCivilianObjection(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            FeedbackReporters(),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            ValidateOpenTasks(MonitorIncomingView),
            WaitForTimer(),
            CheckIncomingView(objection=Objection.NO),
            ValidateOpenTasks(CreateConceptDecision),
        )
