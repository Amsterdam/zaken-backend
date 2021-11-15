from api.tasks.summon import (
    CheckPermitProcedure,
    FinishPermitCheck,
    MonitorIncomingPermitRequest,
    MonitorPermitProcedure,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestMonitorIncomingPermitRequest(DefaultAPITest):
    def test_has_no_permit(self):
        self.get_case().run_steps(
            *MonitorIncomingPermitRequest.get_steps(permit_requested=True),
            MonitorPermitProcedure(),
            ValidateOpenTasks(FinishPermitCheck),
        )

    def test_has_permit(self):
        self.get_case().run_steps(
            *MonitorIncomingPermitRequest.get_steps(permit_requested=True),
            WaitForTimer(),
            ValidateOpenTasks(CheckPermitProcedure),
        )
