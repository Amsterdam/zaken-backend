from api.config import HasPermit
from api.tasks.close_case import PlanNextStep
from api.tasks.summon import (
    CheckPermitProcedure,
    FinishPermitCheck,
    MonitorIncomingPermitRequest,
    ProcessNotice,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestCheckPermitProcedure(DefaultAPITest):
    def test_no(self):
        self.get_case().run_steps(
            *MonitorIncomingPermitRequest.get_steps(permit_requested=True),
            CheckPermitProcedure(has_permit=HasPermit.NO),
            ValidateOpenTasks(ProcessNotice),
        )

    def test_yes(self):
        self.get_case().run_steps(
            *MonitorIncomingPermitRequest.get_steps(permit_requested=True),
            CheckPermitProcedure(has_permit=HasPermit.YES),
            FinishPermitCheck(),
            ValidateOpenTasks(PlanNextStep),
        )
