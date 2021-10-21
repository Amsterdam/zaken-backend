from api.config import HasPermit, SummonTypes
from api.tasks.debrief import CreateConceptNotices
from api.tasks.summon import (
    CheckPermitProcedure,
    MonitorIncomingPermitRequest,
    MonitorPermitProcedure,
    ProcessNotice,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestCivilianNoPermit(DefaultAPITest):
    def test(self):
        self.skipTest("CheckPermitProcedure not found")
        self.get_case().run_steps(
            *ProcessNotice.get_steps(
                type=SummonTypes.HolidayRental.LEGALIZATION_LETTER
            ),
            MonitorIncomingPermitRequest(),
            MonitorPermitProcedure(has_permit=False),
            # WaitForTimer(),
            CheckPermitProcedure(has_permit=HasPermit.NO),
            ValidateOpenTasks(CreateConceptNotices),
        )
