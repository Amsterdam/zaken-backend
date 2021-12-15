from api.config import DecisionType
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.decision import (
    test_contacteren_stadsdeel,
    test_nakijken_besluit,
    test_versturen_invordering_belastingen,
    test_verwerken_definitieve_besluit,
)
from api.tasks.renounce_decision import test_opstellen_concept_voornemen_afzien
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_verwerken_definitieve_besluit_test(DefaultAPITest):
    def test_fine(self):
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(type=DecisionType.Vakantieverhuur.FINE),
            ValidateOpenTasks(test_versturen_invordering_belastingen),
        )

    def test_collection_penalty(self):
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(
                type=DecisionType.Vakantieverhuur.COLLECTION_PENALTY
            ),
            ValidateOpenTasks(test_versturen_invordering_belastingen),
        )

    def test_decision_fine_report_duty(self):
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(
                type=DecisionType.Vakantieverhuur.DECISION_FINE_REPORT_DUTY
            ),
            ValidateOpenTasks(test_versturen_invordering_belastingen),
        )

    def test_preventive_burdon(self):
        """
        In case of PREVENTIVE_BURDEN we don't expect SendTaxCollection or ContactDistrict.
        But we do expect PlanNextStep.
        """
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(
                type=DecisionType.Vakantieverhuur.PREVENTIVE_BURDEN
            ),
            ValidateOpenTasks(test_uitzetten_vervolgstap),
        )

    def test_burden_under_penalty(self):
        """
        In case of BURDEN_UNDER_PENALTY we don't expect SendTaxCollection or ContactDistrict.
        But we do expect PlanNextStep.
        """
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(
                type=DecisionType.Vakantieverhuur.BURDEN_UNDER_PENALTY
            ),
            ValidateOpenTasks(test_uitzetten_vervolgstap),
        )

    def test_revoke_vv_permit(self):
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(
                type=DecisionType.Vakantieverhuur.REVOKE_VV_PERMIT
            ),
            ValidateOpenTasks(test_contacteren_stadsdeel),
        )

    def test_revoke_bb_permit(self):
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(
                type=DecisionType.Vakantieverhuur.REVOKE_BB_PERMIT
            ),
            ValidateOpenTasks(test_contacteren_stadsdeel),
        )

    def test_revoke_shortstay_permit(self):
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(
                type=DecisionType.Vakantieverhuur.REVOKE_SHORTSTAY_PERMIT
            ),
            ValidateOpenTasks(test_contacteren_stadsdeel),
        )

    def test_no_decision(self):
        self.get_case().run_steps(
            *test_nakijken_besluit.get_steps(),
            test_verwerken_definitieve_besluit(
                type=DecisionType.Vakantieverhuur.NO_DECISION
            ),
            ValidateOpenTasks(test_opstellen_concept_voornemen_afzien),
        )
