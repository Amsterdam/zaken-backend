from api.config import Process, RenounceConceptSummon, TypeConceptSummon
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.debrief import test_opstellen_verkorte_rapportage_huisbezoek
from api.tasks.summon import (
    test_afzien_concept_aanschrijving,
    test_nakijken_aanschrijving,
    test_opstellen_concept_aanschrijving,
)
from api.tasks.visit import test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestMultipleSummons(DefaultAPITest):
    def test(self):
        case = self.get_case()
        case.add_process(Process.HolidayRental.ADD_SUMMON),
        case.run_steps(
            ValidateOpenTasks(
                test_inplannen_status, test_opstellen_concept_aanschrijving
            ),
            *test_opstellen_verkorte_rapportage_huisbezoek.get_steps(),
            ValidateOpenTasks(test_opstellen_concept_aanschrijving),
            test_opstellen_concept_aanschrijving(
                type_concept_summon=TypeConceptSummon.RENOUNCE_SUMMON
            ),
            test_afzien_concept_aanschrijving(
                renounce_concept_summon=RenounceConceptSummon.NO_VIOLATION
            ),
            ValidateOpenTasks(test_uitzetten_vervolgstap),
        )
