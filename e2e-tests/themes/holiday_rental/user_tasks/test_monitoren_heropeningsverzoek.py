from api.tasks.closing_procedure import (
    test_beoordelen_heropeningsverzoek,
    test_contacteren_eigenaar_1,
    test_monitoren_heropeningsverzoek,
    test_opslaan_brandweeradvies,
)
from api.test import DefaultAPITest
from api.timers import WaitForTimer
from api.validators import ValidateOpenTasks


class task_monitoren_heropeningsverzoek_test(DefaultAPITest):
    def test_no_reopen(self):
        self.get_case().run_steps(
            *test_opslaan_brandweeradvies.get_steps(),
            test_monitoren_heropeningsverzoek(),
            ValidateOpenTasks(test_beoordelen_heropeningsverzoek),
        )

    def test_reopen(self):
        self.get_case().run_steps(
            *test_opslaan_brandweeradvies.get_steps(),
            WaitForTimer(),
            ValidateOpenTasks(test_contacteren_eigenaar_1),
        )
