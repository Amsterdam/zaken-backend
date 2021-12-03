from api.config import RenounceConceptSummon, TypeConceptSummon
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.summon import (
    test_afzien_concept_aanschrijving,
    test_opstellen_concept_aanschrijving,
)
from api.tasks.visit import test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_afzien_concept_aanschrijving_test(DefaultAPITest):
    def test_new_concept_summon(self):
        self.get_case().run_steps(
            *test_opstellen_concept_aanschrijving.get_steps(
                TypeConceptSummon.RENOUNCE_SUMMON
            ),
            test_afzien_concept_aanschrijving(
                renounce_concept_summon=RenounceConceptSummon.NEW_CONCEPT_SUMMON
            ),
            ValidateOpenTasks(test_opstellen_concept_aanschrijving)
        )

    def test_new_visit_required(self):
        self.get_case().run_steps(
            *test_opstellen_concept_aanschrijving.get_steps(
                TypeConceptSummon.RENOUNCE_SUMMON
            ),
            test_afzien_concept_aanschrijving(
                renounce_concept_summon=RenounceConceptSummon.NEW_VISIT_REQUIRED
            ),
            ValidateOpenTasks(test_inplannen_status)
        )

    def test_no_violation(self):
        self.get_case().run_steps(
            *test_opstellen_concept_aanschrijving.get_steps(
                TypeConceptSummon.RENOUNCE_SUMMON
            ),
            test_afzien_concept_aanschrijving(
                renounce_concept_summon=RenounceConceptSummon.NO_VIOLATION
            ),
            ValidateOpenTasks(test_uitzetten_vervolgstap)
        )
