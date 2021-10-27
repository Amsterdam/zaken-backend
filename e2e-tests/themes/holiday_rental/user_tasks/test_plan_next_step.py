from api.config import DecisionType, NextStep
from api.tasks.close_case import Close, PlanNextStep
from api.tasks.decision import Decision
from api.tasks.visit import ScheduleVisit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestPlanNextStep(DefaultAPITest):
    def test_close(self):
        self.get_case().run_steps(
            *Decision.get_steps(type=DecisionType.HolidayRental.BURDEN_UNDER_PENALTY),
            PlanNextStep(next_step=NextStep.CLOSE),
            ValidateOpenTasks(Close),
        )

    def test_recheck(self):
        self.skipTest("PlanNextStep is not given")
        self.get_case().run_steps(
            *Decision.get_steps(type=DecisionType.HolidayRental.BURDEN_UNDER_PENALTY),
            PlanNextStep(next_step=NextStep.RECHECK),
            ValidateOpenTasks(ScheduleVisit),  # Inplannen hercontrole
        )
