from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class TestTaskCreateSchedule(DefaultAPITest):
    def test(self):
        self.get_case().run_steps(ScheduleVisit(), ValidateOpenTasks(Visit))
