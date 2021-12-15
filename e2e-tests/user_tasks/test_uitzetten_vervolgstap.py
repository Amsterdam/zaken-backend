from api.config import DecisionType, NextStep
from api.tasks.close_case import test_afsluiten_zaak, test_uitzetten_vervolgstap
from api.tasks.decision import test_verwerken_definitieve_besluit
from api.tasks.visit import test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_uitzetten_vervolgstap_test(DefaultAPITest):
    def test_close(self):
        self.get_case().run_steps(
            *test_verwerken_definitieve_besluit.get_steps(
                type=DecisionType.Vakantieverhuur.BURDEN_UNDER_PENALTY
            ),
            test_uitzetten_vervolgstap(next_step=NextStep.CLOSE),
            ValidateOpenTasks(test_afsluiten_zaak),
        )

    def test_recheck(self):
        self.get_case().run_steps(
            *test_verwerken_definitieve_besluit.get_steps(
                type=DecisionType.Vakantieverhuur.BURDEN_UNDER_PENALTY
            ),
            test_uitzetten_vervolgstap(next_step=NextStep.RECHECK),
            ValidateOpenTasks(test_inplannen_status),  # Inplannen hercontrole
        )
