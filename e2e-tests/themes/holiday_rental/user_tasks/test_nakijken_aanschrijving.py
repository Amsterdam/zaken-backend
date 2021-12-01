from api.config import SummonValidity
from api.tasks.summon import (
    test_afzien_concept_aanschrijving,
    test_nakijken_aanschrijving,
    test_opstellen_concept_aanschrijving,
    test_verwerk_aanschrijving,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_nakijken_aanschrijving_test(DefaultAPITest):
    def test_valid(self):
        self.get_case().run_steps(
            *test_opstellen_concept_aanschrijving.get_steps(),
            test_nakijken_aanschrijving(summon_validity=SummonValidity.YES),
            ValidateOpenTasks(test_verwerk_aanschrijving)
        )

    def test_invalid(self):
        self.get_case().run_steps(
            *test_opstellen_concept_aanschrijving.get_steps(),
            test_nakijken_aanschrijving(summon_validity=SummonValidity.NO),
            ValidateOpenTasks(test_afzien_concept_aanschrijving)
        )
