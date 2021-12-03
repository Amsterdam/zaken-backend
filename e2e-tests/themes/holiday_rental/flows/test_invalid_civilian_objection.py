from api.config import DecisionType, ObjectionValid, SummonTypes, Violation
from api.tasks.debrief import (
    test_opstellen_beeldverslag,
    test_opstellen_rapport_van_bevindingen,
    test_terugkoppelen_melder_2,
    test_verwerken_debrief,
)
from api.tasks.decision import (
    test_beoordelen_zienswijze,
    test_nakijken_besluit,
    test_opstellen_concept_besluit,
    test_versturen_invordering_belastingen,
    test_verwerken_definitieve_besluit,
)
from api.tasks.summon import (
    test_monitoren_binnenkomen_zienswijze,
    test_nakijken_aanschrijving,
    test_opstellen_concept_aanschrijving,
    test_verwerk_aanschrijving,
)
from api.tasks.visit import test_doorgeven_status_top, test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateNoOpenTasks


class TestInvalidCivilianObjection(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            test_inplannen_status(),
            test_doorgeven_status_top(),
            test_verwerken_debrief(violation=Violation.YES),
            test_terugkoppelen_melder_2(),
            test_opstellen_beeldverslag(),
            test_opstellen_rapport_van_bevindingen(),
            test_opstellen_concept_aanschrijving(),
            test_nakijken_aanschrijving(),
            test_verwerk_aanschrijving(
                type=SummonTypes.HolidayRental.INTENTION_TO_FINE
            ),
            test_monitoren_binnenkomen_zienswijze(),
            test_beoordelen_zienswijze(objection_valid=ObjectionValid.NO),
            test_opstellen_concept_besluit(),
            test_nakijken_besluit(),
            test_verwerken_definitieve_besluit(type=DecisionType.HolidayRental.FINE),
            test_versturen_invordering_belastingen(),
            ValidateNoOpenTasks(),
            # For now user has to stage another step, in the future we would like to trigger
            # PlanNextStep automatically
            # ValidateOpenTasks(PlanNextStep)
        )
