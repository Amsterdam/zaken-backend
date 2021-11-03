from api.config import PermitRequested
from api.tasks.close_case import PlanNextStep
from api.tasks.summon import CheckPermitProcedure, FinishPermitCheck
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestFinishPermitCheck(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *CheckPermitProcedure.get_steps(permit_requested=PermitRequested.YES),
            FinishPermitCheck(),
            ValidateOpenTasks(PlanNextStep)
        )
