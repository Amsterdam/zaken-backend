from api.config import HasPermit
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.summon import (
    test_controleren_vergunningsprocedure,
    test_monitoren_vergunningsprocedure,
    test_opstellen_concept_aanschrijving,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_controleren_vergunningsprocedure_test(DefaultAPITest):
    def test_no(self):
        self.get_case().run_steps(
            *test_monitoren_vergunningsprocedure.get_steps(has_permit=False),
            test_controleren_vergunningsprocedure(has_permit=HasPermit.NO),
            ValidateOpenTasks(test_opstellen_concept_aanschrijving),
        )

    def test_yes(self):
        self.get_case().run_steps(
            *test_monitoren_vergunningsprocedure.get_steps(has_permit=False),
            test_controleren_vergunningsprocedure(has_permit=HasPermit.YES),
            ValidateOpenTasks(test_uitzetten_vervolgstap),
        )
