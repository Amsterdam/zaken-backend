from api.config import SummonType
from api.tasks.summon import (
    test_controleren_binnenkomst_vergunningaanvraag,
    test_monitoren_binnenkomen_vergunningaanvraag,
    test_monitoren_vergunningsprocedure,
    test_verwerk_aanschrijving,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class task_monitoren_binnenkomen_vergunningaanvraag_test(DefaultAPITest):
    def test_timeout(self):
        self.get_case().run_steps(
            *test_verwerk_aanschrijving.get_steps(
                type=SummonType.Vakantieverhuur.LEGALIZATION_LETTER
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_vergunningaanvraag),
            WaitForTimer(),
            ValidateOpenTasks(test_controleren_binnenkomst_vergunningaanvraag),
        )

    def test_no_timeout(self):
        self.get_case().run_steps(
            *test_verwerk_aanschrijving.get_steps(
                type=SummonType.Vakantieverhuur.LEGALIZATION_LETTER
            ),
            ValidateOpenTasks(test_monitoren_binnenkomen_vergunningaanvraag),
            test_monitoren_binnenkomen_vergunningaanvraag(),
            ValidateOpenTasks(test_monitoren_vergunningsprocedure),
        )
