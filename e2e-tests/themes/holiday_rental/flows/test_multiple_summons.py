from api.config import Process, SummonTypes
from api.tasks.close_case import PlanNextStep
from api.tasks.debrief import HomeVisitReport
from api.tasks.summon import ProcessNotice
from api.tasks.visit import ScheduleVisit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestMultipleSummons(DefaultAPITest):
    def test(self):
        case = self.get_case()
        case.add_process(Process.HolidayRental.ADD_SUMMON),
        case.run_steps(
            ValidateOpenTasks(ScheduleVisit, ProcessNotice),
            *HomeVisitReport.get_steps(),
            ValidateOpenTasks(ProcessNotice),
            ProcessNotice(type=SummonTypes.HolidayRental.WARNING_SS_LICENCE),
            ValidateOpenTasks(PlanNextStep),
        )
