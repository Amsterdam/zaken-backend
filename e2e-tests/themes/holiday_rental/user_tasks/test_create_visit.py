from api.config import Situations
from api.tasks.debrief import Debrief, Visit
from api.tasks.visit import ScheduleVisit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestTaskCreateVisit(DefaultAPITest):
    def test_nobody_present(self):
        self.case.run_steps(
            *ScheduleVisit.get_steps(),
            Visit(
                situation=Situations.NOBODY_PRESENT,
                can_next_visit_go_ahead=True,
            ),
            ValidateOpenTasks(ScheduleVisit),
        )

    def test_no_cooperation(self):
        self.case.run_steps(
            *ScheduleVisit.get_steps(),
            Visit(
                situation=Situations.NO_COOPERATION,
            ),
            ValidateOpenTasks(Debrief),
        )

    def test_access_granted(self):
        self.case.run_steps(
            *ScheduleVisit.get_steps(),
            Visit(
                situation=Situations.ACCESS_GRANTED,
            ),
            ValidateOpenTasks(Debrief),
        )
