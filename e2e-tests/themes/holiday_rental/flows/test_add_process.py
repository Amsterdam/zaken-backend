from api.config import Process
from api.tasks.summon import ProcessNotice
from api.tasks.visit import ScheduleVisit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestAddProcess(DefaultAPITest):
    def test(self):
        case = self.get_case()
        case.run_steps(
            ValidateOpenTasks(ScheduleVisit),
        )
        case.add_process(Process.HolidayRental.ADD_SUMMON),
        case.run_steps(
            ValidateOpenTasks(ScheduleVisit, ProcessNotice),
        )
