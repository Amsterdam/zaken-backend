from api.config import Violation
from api.tasks.debrief import (
    CreateConceptNotices,
    CreateFindingsReport,
    CreatePictureReport,
    Debrief,
    HomeVisitReport,
    RequestAuthorization,
    Visit,
)
from api.tasks.visit import FeedbackReporters, ScheduleVisit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestDebrief(DefaultAPITest):
    def test_send_to_other_theme(self):
        self.skipTest(
            "#BUG: We should feedback the reporters after sending to another team. (actually a new feature request)"
        )
        self.case.run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.SEND_TO_OTHER_THEME),
            ValidateOpenTasks(
                FeedbackReporters,
                HomeVisitReport,
            ),
        )

    def test_violation_no(self):
        self.skipTest("#BUG: We should feedback the reporters")
        self.case.run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.NO),
            ValidateOpenTasks(
                FeedbackReporters,
                HomeVisitReport,
            ),
        )

    def test_violation_yes(self):
        self.case.run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.YES),
            ValidateOpenTasks(
                CreatePictureReport,
                CreateFindingsReport,
                CreateConceptNotices,
            ),
        )

    def test_additional_research_required(self):
        self.case.run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.ADDITIONAL_RESEARCH_REQUIRED),
            ValidateOpenTasks(Debrief),
        )

    def test_additional_visit_required(self):
        self.case.run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.ADDITIONAL_VISIT_REQUIRED),
            ValidateOpenTasks(ScheduleVisit),
        )

    def test_additional_visit_with_authorization(self):
        self.case.run_steps(
            *Visit.get_steps(),
            Debrief(violation=Violation.ADDITIONAL_VISIT_WITH_AUTHORIZATION),
            ValidateOpenTasks(RequestAuthorization),
        )
