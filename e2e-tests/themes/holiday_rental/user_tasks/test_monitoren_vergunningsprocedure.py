from api.tasks.summon import (
    test_afronden_vergunningscheck,
    test_controleren_vergunningsprocedure,
    test_monitoren_binnenkomen_vergunningaanvraag,
    test_monitoren_vergunningsprocedure,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class task_monitoren_vergunningsprocedure_test(DefaultAPITest):
    def test_has_no_permit(self):
        self.get_case().run_steps(
            *test_monitoren_binnenkomen_vergunningaanvraag.get_steps(
                permit_requested=True
            ),
            test_monitoren_vergunningsprocedure(),
            ValidateOpenTasks(test_afronden_vergunningscheck),
        )

    def test_has_permit(self):
        self.get_case().run_steps(
            *test_monitoren_binnenkomen_vergunningaanvraag.get_steps(
                permit_requested=True
            ),
            WaitForTimer(),
            ValidateOpenTasks(test_controleren_vergunningsprocedure),
        )
