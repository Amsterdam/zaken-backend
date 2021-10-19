from api.config import SummonTypes, Violation
from api.tasks.debrief import (
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
)
from api.tasks.summon import CheckNotices, MonitorIncomingView, ProcessNotice
from api.tasks.visit import FeedbackReporters, ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestNoCivilianObjection(DefaultAPITest):
    def test(self):
        self.skipTest("#BUG: Missing FeedbackReporters")
        self.case.run_steps(
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            FeedbackReporters(),  # BUG in Spiff. According to Nicoline if Violation=True, we should Feedback the reporters
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            ValidateOpenTasks(MonitorIncomingView),
            # Cannot test because of timer!
            # WaitForTimer(MonitorIncomingView(objection=False)),
            # MonitorIncomingView(objection=False),
            # CheckIncomingView(objection=Objection.NO),
            # AssertNumberOfOpenTasks(0),
        )
