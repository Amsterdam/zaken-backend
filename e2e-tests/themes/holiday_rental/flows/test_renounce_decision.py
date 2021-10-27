from api.config import DecisionType
from api.tasks.close_case import PlanNextStep
from api.tasks.decision import CheckConceptDecision, Decision
from api.tasks.renounce_decision import (
    CheckRenounceLetter,
    CreateConceptRenounce,
    CreateDefinitiveRenounce,
)
from api.test import DefaultAPITest


class TestRenounceDecision(DefaultAPITest):
    def test(self):
        """
        This flow only tests one Summon/Decision.
        """
        self.skipTest("PlanNextStep not given")
        self.get_case().run_steps(
            *CheckConceptDecision.get_steps(),
            Decision(type=DecisionType.HolidayRental.NO_DECISION),
            CreateConceptRenounce(),
            CheckRenounceLetter(),
            CreateDefinitiveRenounce(),
            PlanNextStep(),
        )
