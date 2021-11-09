from api.config import HasPermit
from api.tasks.close_case import PlanNextStep
from api.tasks.summon import CheckPermitProcedure, FinishPermitCheck
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestFinishPermitCheck(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *CheckPermitProcedure.get_steps(has_permit=HasPermit.YES),
            FinishPermitCheck(),
            ValidateOpenTasks(PlanNextStep)
        )
