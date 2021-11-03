from api.config import HasPermit
from api.tasks.summon import (
    CheckPermitProcedure,
    MonitorIncomingPermitRequest,
    MonitorPermitProcedure,
    ProcessNotice,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestCheckPermitProcedure(DefaultAPITest):
    def test_no(self):
        self.get_case().run_steps(
            *MonitorIncomingPermitRequest.get_steps(permit_requested=False),
            CheckPermitProcedure(has_permit=HasPermit.NO),
            ValidateOpenTasks(ProcessNotice),
        )

    def test_yes(self):
        self.get_case().run_steps(
            *MonitorIncomingPermitRequest.get_steps(permit_requested=False),
            CheckPermitProcedure(has_permit=HasPermit.YES),
            ValidateOpenTasks(MonitorPermitProcedure),
        )
