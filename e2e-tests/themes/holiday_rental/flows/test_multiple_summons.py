from api.config import Process, SummonTypes
from api.tasks.close_case import test_uitzetten_vervolgstap
from api.tasks.debrief import test_opstellen_verkorte_rapportage_huisbezoek
from api.tasks.summon import test_verwerk_aanschrijving
from api.tasks.visit import test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestMultipleSummons(DefaultAPITest):
    def test(self):
        case = self.get_case()
        case.add_process(Process.HolidayRental.ADD_SUMMON),
        case.run_steps(
            ValidateOpenTasks(test_inplannen_status, test_verwerk_aanschrijving),
            *test_opstellen_verkorte_rapportage_huisbezoek.get_steps(),
            ValidateOpenTasks(test_verwerk_aanschrijving),
            test_verwerk_aanschrijving(
                type=SummonTypes.HolidayRental.WARNING_SS_LICENCE
            ),
            ValidateOpenTasks(test_uitzetten_vervolgstap),
        )
