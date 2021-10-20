from api.config import Violation
from api.tasks.debrief import (
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    HomeVisitReport,
    Visit,
    WaitInternalResearch,
)
from api.tasks.director import FeedbackReporters
from api.tasks.visit import RequestAuthorization, ScheduleVisit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestDebrief(DefaultAPITest):
    def test_send_to_other_theme(self):
        self.get_case().run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.SEND_TO_OTHER_THEME),
            ValidateOpenTasks(
                FeedbackReporters,
                HomeVisitReport,
            ),
        )

    def test_violation_no(self):
        self.get_case().run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.NO),
            ValidateOpenTasks(
                FeedbackReporters,
                HomeVisitReport,
            ),
        )

    def test_violation_yes(self):
        self.get_case().run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.YES),
            ValidateOpenTasks(
                CreatePictureReport,
                CreateFindingsReport,
                CreateConceptNotices,
            ),
        )

    def test_additional_research_required(self):
        self.get_case().run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.ADDITIONAL_RESEARCH_REQUIRED),
            ValidateOpenTasks(WaitInternalResearch),
        )

    def test_additional_visit_required(self):
        self.skipTest("Instead of ScheduleVisit, another Debrief is given. @xavier")
        self.get_case().run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.ADDITIONAL_VISIT_REQUIRED),
            ValidateOpenTasks(ScheduleVisit),
        )

    def test_additional_visit_with_authorization(self):
        self.skipTest(
            "Instead of RequestAuthorization, another Debrief is given. @xavier"
        )
        self.get_case().run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.ADDITIONAL_VISIT_WITH_AUTHORIZATION),
            ValidateOpenTasks(RequestAuthorization),
        )
