from api.config import TypeConceptSummon
from api.tasks.summon import (
    test_afzien_concept_aanschrijving,
    test_nakijken_aanschrijving,
    test_opstellen_beeldverslag,
    test_opstellen_concept_aanschrijving,
    test_opstellen_rapport_van_bevindingen,
    test_terugkoppelen_melder_2,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_opstellen_concept_aanschrijving(DefaultAPITest):
    def test_renounce(self):
        self.get_case().run_steps(
            *test_opstellen_beeldverslag.get_steps(),
            test_opstellen_rapport_van_bevindingen(),
            test_opstellen_concept_aanschrijving(
                type_concept_summon=TypeConceptSummon.RENOUNCE_SUMMON
            ),
            ValidateOpenTasks(test_afzien_concept_aanschrijving)
        )

    def test_other(self):
        self.get_case().run_steps(
            *test_opstellen_beeldverslag.get_steps(),
            test_opstellen_rapport_van_bevindingen(),
            test_opstellen_concept_aanschrijving(
                type_concept_summon=TypeConceptSummon.OTHER_SUMMON
            ),
            ValidateOpenTasks(test_nakijken_aanschrijving)
        )
