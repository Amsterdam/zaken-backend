from api.config import SummonTypes
from api.tasks.summon import (
    test_beoordelen_zienswijze,
    test_controleren_binnenkomst_zienswijze,
    test_monitoren_binnenkomen_zienswijze,
    test_verwerk_aanschrijving,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class task_controleren_binnenkomst_zienswijze_test(DefaultAPITest):
    def test_timer(self):
        self.get_case().run_steps(
            *test_verwerk_aanschrijving.get_steps(
                SummonTypes.HolidayRental.INTENTION_TO_FINE
            ),
            WaitForTimer(),
            ValidateOpenTasks(test_controleren_binnenkomst_zienswijze),
        )

    def test_no_timer(self):
        self.get_case().run_steps(
            *test_verwerk_aanschrijving.get_steps(
                SummonTypes.HolidayRental.INTENTION_TO_FINE
            ),
            test_monitoren_binnenkomen_zienswijze(),
            ValidateOpenTasks(test_beoordelen_zienswijze),
        )
