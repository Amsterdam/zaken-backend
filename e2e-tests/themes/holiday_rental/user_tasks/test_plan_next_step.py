from api.config import NextStep, SummonTypes
from api.tasks.close_case import Close, PlanNextStep
from api.tasks.summon import ProcessNotice
from api.tasks.visit import ScheduleVisit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestPlanNextStep(DefaultAPITest):
    def test_close(self):
        self.get_case().run_steps(
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.WARNING_LETTER),
            PlanNextStep(next_step=NextStep.CLOSE),
            ValidateOpenTasks(Close),
        )

    def test_recheck(self):
        self.get_case().run_steps(
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.WARNING_LETTER),
            PlanNextStep(next_step=NextStep.RECHECK),
            ValidateOpenTasks(ScheduleVisit),
        )

    def test_renounce(self):
        self.skipTest(
            "BUG: Not sure if/how this should work. Is renounce even supported as a 'next-step'?"
        )
        self.get_case().run_steps(
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.WARNING_LETTER),
            PlanNextStep(next_step=NextStep.RENOUNCE),
            # ValidateOpenTasks(??),
        )
