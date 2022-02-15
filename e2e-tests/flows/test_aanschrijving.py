from api.config import SummonType, Violation
from api.tasks.debrief import (
    test_opstellen_beeldverslag,
    test_opstellen_rapport_van_bevindingen,
    test_terugkoppelen_melder_2,
    test_verwerken_debrief,
)
from api.tasks.summon import (
    test_monitoren_binnenkomen_vergunningaanvraag,
    test_nakijken_aanschrijving,
    test_opstellen_concept_aanschrijving,
    test_verwerk_aanschrijving,
)
from api.tasks.visit import test_doorgeven_status_top, test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestViolationLegalizationLetter(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            test_inplannen_status(),
            test_doorgeven_status_top(),
            test_verwerken_debrief(violation=Violation.YES),
            ValidateOpenTasks(
                test_opstellen_rapport_van_bevindingen,
                test_opstellen_beeldverslag,
            ),
            test_terugkoppelen_melder_2(),
            test_opstellen_beeldverslag(),
            test_opstellen_rapport_van_bevindingen(),
            test_opstellen_concept_aanschrijving(),
            test_nakijken_aanschrijving(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.LEGALIZATION_LETTER
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_vergunningaanvraag),
        )
