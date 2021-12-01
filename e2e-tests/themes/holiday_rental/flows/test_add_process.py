from api.config import Process
from api.tasks.summon import test_nakijken_aanschrijving, test_verwerk_aanschrijving
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestAddProcess(DefaultAPITest):
    def test(self):
        case = self.get_case()
        case.run_steps(
            *test_nakijken_aanschrijving.get_steps(),
        )
        case.add_process(Process.HolidayRental.ADD_SUMMON),
        case.run_steps(
            ValidateOpenTasks(test_verwerk_aanschrijving, test_verwerk_aanschrijving),
        )
