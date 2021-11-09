from api.config import Violation
from api.tasks.close_case import Close, PlanNextStep
from api.tasks.debrief import Debrief, HomeVisitReport, InformReporterNoViolation
from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestTimeline(DefaultAPITest):
    def test_no_identification(self):
        case = self.get_case()
        case.run_steps(ScheduleVisit(), ValidateOpenTasks(Visit))
        events = self.client.get_case_events(case.data["id"])
        self.assertEqual(2, len(case.timeline), len(events))
        self.assertEqual(2, len(events))

    def test_home_visit_report(self):
        self.get_case().run_steps(
            ScheduleVisit(),
            Visit(),
            Debrief(violation=Violation.NO),
            InformReporterNoViolation(),
            HomeVisitReport(),
            PlanNextStep(),
            Close(),
        )


class TestTimelineWithIdentification(DefaultAPITest):
    def get_case_data(self):
        return {
            "identification": 123,
        }

    def test(self):
        case = self.get_case()
        case.run_steps(ScheduleVisit(), ValidateOpenTasks(Visit))
        events = self.client.get_case_events(case.data["id"])
        self.assertEqual(len(case.timeline), len(events))
        self.assertEqual(3, len(events))
