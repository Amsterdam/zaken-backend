from api.config import SummonTypes
from api.tasks.summon import (
    CheckIncomingPermitRequest,
    MonitorIncomingPermitRequest,
    MonitorPermitProcedure,
    ProcessNotice,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestMonitorIncomingPermitRequest(DefaultAPITest):
    def test_timeout(self):
        self.get_case().run_steps(
            *ProcessNotice.get_steps(
                type=SummonTypes.HolidayRental.LEGALIZATION_LETTER
            ),
            ValidateOpenTasks(MonitorIncomingPermitRequest),
            WaitForTimer(),
            ValidateOpenTasks(CheckIncomingPermitRequest),
        )

    def test_no_timeout(self):
        self.get_case().run_steps(
            *ProcessNotice.get_steps(
                type=SummonTypes.HolidayRental.LEGALIZATION_LETTER
            ),
            ValidateOpenTasks(MonitorIncomingPermitRequest),
            MonitorIncomingPermitRequest(objection_valid=True),
            ValidateOpenTasks(MonitorPermitProcedure),
        )
