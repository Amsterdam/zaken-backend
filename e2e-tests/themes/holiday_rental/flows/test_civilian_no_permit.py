from api.config import PermitRequested, SummonTypes
from api.tasks.summon import (
    CheckIncomingPermitRequest,
    MonitorIncomingPermitRequest,
    ProcessNotice,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestCivilianNoPermit(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *ProcessNotice.get_steps(
                type=SummonTypes.HolidayRental.LEGALIZATION_LETTER
            ),
            ValidateOpenTasks(MonitorIncomingPermitRequest),
            WaitForTimer(),
            CheckIncomingPermitRequest(permit_requested=PermitRequested.NO),
            ValidateOpenTasks(ProcessNotice),
        )
