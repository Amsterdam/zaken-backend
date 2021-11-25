from api.config import (
    NextStep,
    ReopenRequest,
    ReviewReopenRequest,
    SummonTypes,
    Violation,
)
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
    test_opstellen_beeldverslag,
    test_opstellen_concept_aanschrijvingen,
    test_opstellen_rapport_van_bevindingen,
    test_terugkoppelen_melder_2,
    test_verwerken_debrief,
)
from api.tasks.summon import test_nakijken_aanschrijvingen, test_verwerk_aanschrijving
from api.tasks.visit import test_doorgeven_status_top, test_inplannen_status
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestViolationClosure(DefaultAPITest):
    def test_direct(self):
        self.get_case().run_steps(
            test_inplannen_status(),
            test_doorgeven_status_top(),
            test_verwerken_debrief(violation=Violation.YES),
            test_terugkoppelen_melder_2(),
            test_opstellen_beeldverslag(),
            test_opstellen_rapport_van_bevindingen(),
            test_opstellen_concept_aanschrijvingen(),
            ValidateOpenTasks(test_nakijken_aanschrijvingen),
            test_nakijken_aanschrijvingen(),
            test_verwerk_aanschrijving(type=SummonTypes.HolidayRental.CLOSURE),
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
