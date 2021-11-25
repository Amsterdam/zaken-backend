from api.config import HasPermit
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.summon import (
    test_afronden_vergunningscheck,
    test_controleren_vergunningsprocedure,
)
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_afronden_vergunningscheck_test(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(
            *test_controleren_vergunningsprocedure.get_steps(has_permit=HasPermit.YES),
            test_afronden_vergunningscheck(),
            ValidateOpenTasks(test_uitzetten_vervolgstap)
        )
