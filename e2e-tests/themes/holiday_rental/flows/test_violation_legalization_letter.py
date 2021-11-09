from api.config import SummonTypes, Violation
from api.tasks.debrief import (
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    InformReporter,
)
from api.tasks.summon import CheckNotices, MonitorIncomingPermitRequest, ProcessNotice
from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestViolationLegalizationLetter(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.YES),
            InformReporter(),
            ValidateOpenTasks(
                CreateFindingsReport, CreatePictureReport, CreateConceptNotices
            ),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            CheckNotices(),
            ProcessNotice(type=SummonTypes.HolidayRental.LEGALIZATION_LETTER),
            ValidateOpenTasks(MonitorIncomingPermitRequest),
        )
