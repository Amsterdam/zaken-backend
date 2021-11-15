from api.config import Process
from api.tasks.debrief import CheckNotices
from api.tasks.summon import ProcessNotice
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestAddProcess(DefaultAPITest):
    def test(self):
        case = self.get_case()
        case.run_steps(
            *CheckNotices.get_steps(),
        )
        case.add_process(Process.HolidayRental.ADD_SUMMON),
        case.run_steps(
            ValidateOpenTasks(ProcessNotice, ProcessNotice),
        )
