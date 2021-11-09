from api.config import SummonTypes
from api.tasks.summon import (
    CheckIncomingView,
    JudgeView,
    MonitorIncomingView,
    ProcessNotice,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class TestMonitorIncomingView(DefaultAPITest):
    def test_timer(self):
        self.get_case().run_steps(
            *ProcessNotice.get_steps(SummonTypes.HolidayRental.INTENTION_TO_FINE),
            WaitForTimer(),
            ValidateOpenTasks(CheckIncomingView),
        )

    def test_no_timer(self):
        self.get_case().run_steps(
            *ProcessNotice.get_steps(SummonTypes.HolidayRental.INTENTION_TO_FINE),
            MonitorIncomingView(),
            ValidateOpenTasks(JudgeView),
        )
