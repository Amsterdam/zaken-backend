from api.config import Process, RenounceConceptSummon, SummonType, TypeConceptSummon
from api.tasks.debrief import test_opstellen_verkorte_rapportage_huisbezoek
from api.tasks.summon import (
    test_afzien_concept_aanschrijving,
    test_monitoren_binnenkomen_vergunningaanvraag,
    test_monitoren_vergunningsprocedure,
    test_nakijken_aanschrijving,
    test_opstellen_concept_aanschrijving,
    test_verwerk_aanschrijving,
)
from api.tasks.visit import test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestCongregateGateway(DefaultAPITest):
    def test_unsupported_order(self):
        """
        Users should not add a new summon to a case that has no debrief yet. But
        would still be nice to support it.
        """
        case = self.get_case()
        case.add_process(Process.HolidayRental.ADD_SUMMON),
        case.run_steps(
            *test_opstellen_verkorte_rapportage_huisbezoek.get_steps(),  # next_step = close-case
            test_opstellen_concept_aanschrijving(
                type_concept_summon=TypeConceptSummon.RENOUNCE_SUMMON
            ),
            test_afzien_concept_aanschrijving(
                renounce_concept_summon=RenounceConceptSummon.NEW_VISIT_REQUIRED
            ),
            ValidateOpenTasks(test_inplannen_status),
        )

    def test_two_summons(self):
        """
        Send warning letter and Renounce concept summon with new visit required
        """
        # create case that will go to visit flow
        case = self.get_case()
        case.run_steps(
            *test_opstellen_concept_aanschrijving.get_steps(
                type_concept_summon=TypeConceptSummon.RENOUNCE_SUMMON
            ),
            test_afzien_concept_aanschrijving(
                renounce_concept_summon=RenounceConceptSummon.NEW_VISIT_REQUIRED
            ),
        )
        # add summon that will go to close-case
        case.add_process(Process.HolidayRental.ADD_SUMMON),
        case.run_steps(
            test_opstellen_concept_aanschrijving(),
            test_nakijken_aanschrijving(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.WARNING_BB_LICENSE
            ),
            ValidateOpenTasks(test_inplannen_status),
        )

    def test_two_summons_via_controleren_vergunningsprocedure(self):
        """
        TODO
        """
        # create case that will go to caseclose flow
        case = self.get_case()
        case.run_steps(
            *test_monitoren_binnenkomen_vergunningaanvraag.get_steps(),
        )
        # add summon that will go to visit flow
        case.add_process(Process.HolidayRental.ADD_SUMMON),

        # finish first flow (to caseclose)
        case.run_steps(
            test_monitoren_vergunningsprocedure(),  # yes got permit
        )

        # finish second flow (to visit)
        case.run_steps(
            test_opstellen_concept_aanschrijving(
                type_concept_summon=TypeConceptSummon.RENOUNCE_SUMMON
            ),
            test_afzien_concept_aanschrijving(
                renounce_concept_summon=RenounceConceptSummon.NEW_VISIT_REQUIRED
            ),
            ValidateOpenTasks(test_inplannen_status),
        )
