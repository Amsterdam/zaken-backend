from api.config import DecisionType
from api.tasks.close_case import PlanNextStep
from api.tasks.decision import (
    CheckConceptDecision,
    ContactDistrict,
    Decision,
    SendTaxCollection,
)
from api.tasks.renounce_decision import CreateConceptRenounce
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestCreateDecision(DefaultAPITest):
    def test_fine(self):
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.FINE),
            ValidateOpenTasks(SendTaxCollection),
        )

    def test_collection_penalty(self):
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.COLLECTION_PENALTY),
            ValidateOpenTasks(SendTaxCollection),
        )

    def test_decision_fine_report_duty(self):
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.DECISION_FINE_REPORT_DUTY),
            ValidateOpenTasks(SendTaxCollection),
        )

    def test_preventive_burdon(self):
        """
        In case of PREVENTIVE_BURDEN we don't expect SendTaxCollection or ContactDistrict.
        But we do expect PlanNextStep.
        """
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.PREVENTIVE_BURDEN),
            ValidateOpenTasks(PlanNextStep),
        )

    def test_burden_under_penalty(self):
        """
        In case of BURDEN_UNDER_PENALTY we don't expect SendTaxCollection or ContactDistrict.
        But we do expect PlanNextStep.
        """
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.BURDEN_UNDER_PENALTY),
            ValidateOpenTasks(PlanNextStep),
        )

    def test_revoke_vv_permit(self):
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.REVOKE_VV_PERMIT),
            ValidateOpenTasks(ContactDistrict),
        )

    def test_revoke_bb_permit(self):
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.REVOKE_BB_PERMIT),
            ValidateOpenTasks(ContactDistrict),
        )

    def test_revoke_shortstay_permit(self):
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.REVOKE_SHORTSTAY_PERMIT),
            ValidateOpenTasks(ContactDistrict),
        )

    def test_no_decision(self):
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.NO_DECISION),
            ValidateOpenTasks(CreateConceptRenounce),
        )
