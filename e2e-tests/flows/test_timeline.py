from api.config import Violation
from api.tasks.close_case import test_close_case, test_uitzetten_vervolgstap
from api.tasks.debrief import (
    test_create_debrief,
    test_opstellen_verkorte_rapportage_huisbezoek,
)
from api.tasks.visit import (
    test_bepalen_processtap_vv,
    test_doorgeven_status_top,
    test_inplannen_status,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestTimeline(DefaultAPITest):
    def test_no_identification(self):
        case = self.get_case()
        case.run_steps(
            test_bepalen_processtap_vv(),
            test_inplannen_status(),
            ValidateOpenTasks(test_doorgeven_status_top),
        )
        events = self.client.get_case_events(case.data["id"])
        self.assertEqual(3, len(case.timeline), len(events))
        self.assertEqual(3, len(events))

    def test_home_visit_report(self):
        self.get_case().run_steps(
            test_bepalen_processtap_vv(),
            test_inplannen_status(),
            test_doorgeven_status_top(),
            test_create_debrief(violation=Violation.NO),
            test_opstellen_verkorte_rapportage_huisbezoek(),
            test_uitzetten_vervolgstap(),
            test_close_case(),
        )


class TestTimelineWithIdentification(DefaultAPITest):
    def get_case_data(self):
        return {
            "identification": 123,
        }

    def test(self):
        case = self.get_case()
        case.run_steps(
            test_bepalen_processtap_vv(),
            test_inplannen_status(),
            ValidateOpenTasks(test_doorgeven_status_top),
        )
        events = self.client.get_case_events(case.data["id"])
        self.assertEqual(
            len(case.timeline),
            len(events),
        )
        self.assertEqual(4, len(events))
