from api.config import DecisionType, ObjectionValid, SummonType, Violation
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.debrief import (
    test_create_debrief,
    test_opstellen_beeldverslag,
    test_opstellen_rapport_van_bevindingen,
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
from api.tasks.visit import (
    test_bepalen_processtap_vv,
    test_doorgeven_status_top,
    test_inplannen_status,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestInvalidCivilianObjection(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            test_bepalen_processtap_vv(),
            test_inplannen_status(),
            test_doorgeven_status_top(),
            test_create_debrief(violation=Violation.YES),
            test_opstellen_beeldverslag(),
            test_opstellen_rapport_van_bevindingen(),
            test_opstellen_concept_aanschrijving(),
            test_nakijken_aanschrijving(),
            test_verwerk_aanschrijving(
                type=SummonType.Vakantieverhuur.INTENTION_TO_FINE
            ),
            test_monitoren_binnenkomen_zienswijze(),
            test_beoordelen_zienswijze(objection_valid=ObjectionValid.NO),
            test_opstellen_concept_besluit(),
            test_nakijken_besluit(),
            test_verwerken_definitieve_besluit(type=DecisionType.Vakantieverhuur.FINE),
            test_versturen_invordering_belastingen(),
            ValidateOpenTasks(test_uitzetten_vervolgstap),
        )
