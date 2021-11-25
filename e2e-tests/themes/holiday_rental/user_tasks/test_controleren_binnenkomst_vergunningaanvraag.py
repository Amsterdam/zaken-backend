from api.config import PermitRequested
from api.tasks.summon import (
    test_controleren_binnenkomst_vergunningaanvraag,
    test_monitoren_binnenkomen_vergunningaanvraag,
    test_monitoren_vergunningsprocedure,
    test_verwerk_aanschrijving,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_controleren_binnenkomst_vergunningaanvraag_test(DefaultAPITest):
    def test_permit_requested(self):
        self.get_case().run_steps(
            *test_monitoren_binnenkomen_vergunningaanvraag.get_steps(
                permit_requested=False
            ),
            test_controleren_binnenkomst_vergunningaanvraag(
                permit_requested=PermitRequested.YES
            ),
            ValidateOpenTasks(test_monitoren_vergunningsprocedure),
        )

    def test_no_permit_requested(self):
        self.get_case().run_steps(
            *test_monitoren_binnenkomen_vergunningaanvraag.get_steps(
                permit_requested=False
            ),
            test_controleren_binnenkomst_vergunningaanvraag(
                permit_requested=PermitRequested.NO
            ),
            ValidateOpenTasks(test_verwerk_aanschrijving),
        )
