from api.config import Violation
from api.tasks.debrief import (
    test_afwachten_intern_onderzoek,
    test_create_debrief,
    test_opstellen_beeldverslag,
    test_opstellen_rapport_van_bevindingen,
    test_opstellen_verkorte_rapportage_huisbezoek,
)
from api.tasks.visit import (
    test_aanvragen_machtiging,
    test_doorgeven_status_top,
    test_inplannen_status,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_verwerken_debrief_test(DefaultAPITest):
    def test_send_to_other_theme(self):
        self.get_case().run_steps(
            *test_doorgeven_status_top.get_steps(),
            test_create_debrief(violation=Violation.SEND_TO_OTHER_THEME),
            ValidateOpenTasks(
                test_opstellen_verkorte_rapportage_huisbezoek,
            ),
        )

    def test_violation_no(self):
        self.get_case().run_steps(
            *test_doorgeven_status_top.get_steps(),
            test_create_debrief(violation=Violation.NO),
            ValidateOpenTasks(
                test_opstellen_verkorte_rapportage_huisbezoek,
            ),
        )

    def test_violation_yes(self):
        self.get_case().run_steps(
            *test_doorgeven_status_top.get_steps(),
            test_create_debrief(violation=Violation.YES),
            ValidateOpenTasks(
                test_opstellen_beeldverslag,
                test_opstellen_rapport_van_bevindingen,
            ),
        )

    def test_additional_research_required(self):
        self.get_case().run_steps(
            *test_doorgeven_status_top.get_steps(),
            test_create_debrief(violation=Violation.ADDITIONAL_RESEARCH_REQUIRED),
            ValidateOpenTasks(test_afwachten_intern_onderzoek),
        )

    def test_additional_visit_required(self):
        self.get_case().run_steps(
            *test_doorgeven_status_top.get_steps(),
            test_create_debrief(violation=Violation.ADDITIONAL_VISIT_REQUIRED),
            ValidateOpenTasks(test_inplannen_status),
        )

    def test_additional_visit_with_authorization(self):
        self.get_case().run_steps(
            *test_doorgeven_status_top.get_steps(),
            test_create_debrief(
                violation=Violation.ADDITIONAL_VISIT_WITH_AUTHORIZATION
            ),
            ValidateOpenTasks(test_aanvragen_machtiging),
        )
