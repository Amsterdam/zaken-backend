from api.config import PermitRequested
from api.tasks.summon import (
    CheckIncomingPermitRequest,
    MonitorIncomingPermitRequest,
    MonitorPermitProcedure,
    ProcessNotice,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestMonitorIncomingPermitRequest(DefaultAPITest):
    def test_permit_requested(self):
        self.get_case().run_steps(
            *MonitorIncomingPermitRequest.get_steps(permit_requested=False),
            CheckIncomingPermitRequest(permit_requested=PermitRequested.YES),
            ValidateOpenTasks(MonitorPermitProcedure),
        )

    def test_no_permit_requested(self):
        self.get_case().run_steps(
            *MonitorIncomingPermitRequest.get_steps(permit_requested=False),
            CheckIncomingPermitRequest(permit_requested=PermitRequested.NO),
            ValidateOpenTasks(ProcessNotice),
        )
