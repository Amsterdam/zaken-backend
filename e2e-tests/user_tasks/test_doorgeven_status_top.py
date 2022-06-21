from api.config import Situations
from api.tasks.debrief import test_create_debrief
from api.tasks.visit import test_doorgeven_status_top, test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks


class task_doorgeven_status_top_test(DefaultAPITest):
    def test_nobody_present_yes_next_visit(self):
        self.get_case().run_steps(
            *test_inplannen_status.get_steps(),
            test_doorgeven_status_top(
                situation=Situations.NOBODY_PRESENT,
                can_next_visit_go_ahead=True,
            ),
            ValidateOpenTasks(test_inplannen_status),
        )

    def test_nobody_present_no_next_visit(self):
        self.get_case().run_steps(
            *test_inplannen_status.get_steps(),
            test_doorgeven_status_top(
                situation=Situations.NOBODY_PRESENT,
                can_next_visit_go_ahead=False,
            ),
            ValidateOpenTasks(test_create_debrief),
        )

    def test_no_cooperation(self):
        self.get_case().run_steps(
            *test_inplannen_status.get_steps(),
            test_doorgeven_status_top(
                situation=Situations.NO_COOPERATION,
                can_next_visit_go_ahead=False,
            ),
            ValidateOpenTasks(test_create_debrief),
        )

    def test_access_granted(self):
        self.get_case().run_steps(
            *test_inplannen_status.get_steps(),
            test_doorgeven_status_top(
                situation=Situations.ACCESS_GRANTED,
            ),
            ValidateOpenTasks(test_create_debrief),
        )
