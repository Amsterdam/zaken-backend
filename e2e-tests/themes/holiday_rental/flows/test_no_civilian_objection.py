from api.config import ObjectionReceived, SummonTypes, Violation
from api.tasks.debrief import (
    test_opstellen_beeldverslag,
    test_opstellen_rapport_van_bevindingen,
    test_terugkoppelen_melder_2,
    test_verwerken_debrief,
)
from api.tasks.decision import test_opstellen_concept_besluit
from api.tasks.director import test_terugkoppelen_melder
from api.tasks.summon import (
    test_controleren_binnenkomst_zienswijze,
    test_monitoren_binnenkomen_zienswijze,
    test_nakijken_aanschrijving,
    test_opstellen_concept_aanschrijving,
    test_verwerk_aanschrijving,
)
from api.tasks.visit import test_doorgeven_status_top, test_inplannen_status
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestNoCivilianObjection(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            test_inplannen_status(),
            test_doorgeven_status_top(),
            test_verwerken_debrief(violation=Violation.YES),
            test_terugkoppelen_melder(),
            test_terugkoppelen_melder_2(),
            test_opstellen_beeldverslag(),
            test_opstellen_rapport_van_bevindingen(),
            test_opstellen_concept_aanschrijving(),
            test_nakijken_aanschrijving(),
            test_verwerk_aanschrijving(
                type=SummonTypes.HolidayRental.INTENTION_TO_FINE
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_zienswijze),
            WaitForTimer(),
            test_controleren_binnenkomst_zienswijze(objection=ObjectionReceived.NO),
            ValidateOpenTasks(test_opstellen_concept_besluit),
        )
