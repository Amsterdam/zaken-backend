from api.config import NextStep, ReviewReopenRequest, SummonType, Violation
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.closing_procedure import (
    test_beoordelen_heropeningsverzoek,
    test_contacteren_eigenaar_1,
    test_contacteren_eigenaar_2,
    test_monitoren_heropeningsverzoek,
    test_monitoren_nieuw_heropeningsverzoek,
    test_opslaan_brandweeradvies,
    test_opslaan_heropeningsverzoek,
    test_opslaan_sleutelteruggave_formulier,
)
from api.tasks.debrief import (
    test_create_debrief,
    test_opstellen_beeldverslag,
    test_opstellen_rapport_van_bevindingen,
)
from api.tasks.summon import (
    test_nakijken_aanschrijving,
    test_opstellen_concept_aanschrijving,
    test_verwerk_aanschrijving,
)
from api.tasks.visit import (
    test_bepalen_processtap_vv,
    test_doorgeven_status_top,
    test_inplannen_status,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestViolationClosure(DefaultAPITest):
    def test_direct(self):
        self.get_case().run_steps(
            test_bepalen_processtap_vv(),
            test_inplannen_status(),
            test_doorgeven_status_top(),
            test_create_debrief(violation=Violation.YES),
            test_opstellen_beeldverslag(),
            test_opstellen_rapport_van_bevindingen(),
            test_opstellen_concept_aanschrijving(),
            ValidateOpenTasks(test_nakijken_aanschrijving),
            test_nakijken_aanschrijving(),
            test_verwerk_aanschrijving(type=SummonType.Vakantieverhuur.CLOSURE),
            test_opslaan_brandweeradvies(),
            test_monitoren_heropeningsverzoek(),
            test_beoordelen_heropeningsverzoek(
                review_request=ReviewReopenRequest.DECLINED
            ),
            test_monitoren_nieuw_heropeningsverzoek(),
            test_beoordelen_heropeningsverzoek(),
            test_opslaan_heropeningsverzoek(),
            test_opslaan_sleutelteruggave_formulier(),
            test_uitzetten_vervolgstap(next_step=NextStep.RECHECK),
            ValidateOpenTasks(test_inplannen_status),
        )

    def test_timer(self):
        self.get_case().run_steps(
            *test_opslaan_brandweeradvies.get_steps(),
            WaitForTimer(),
            test_contacteren_eigenaar_1(),
            ValidateOpenTasks(test_monitoren_heropeningsverzoek),
        )

    def test_timer_second(self):
        self.get_case().run_steps(
            *test_opslaan_brandweeradvies.get_steps(),
            test_monitoren_heropeningsverzoek(),
            test_beoordelen_heropeningsverzoek(
                review_request=ReviewReopenRequest.DECLINED
            ),
            WaitForTimer(),
            test_contacteren_eigenaar_2(),
            ValidateOpenTasks(test_monitoren_nieuw_heropeningsverzoek),
        )
