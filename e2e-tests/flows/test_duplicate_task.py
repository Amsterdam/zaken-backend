import datetime
import logging

from api.config import Situations, Violation
from api.tasks import GenericUserTask
from api.tasks.debrief import test_afwachten_intern_onderzoek, test_create_debrief
from api.tasks.visit import test_doorgeven_status_top, test_inplannen_status
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks

logger = logging.getLogger(__name__)


class TestDuplicateTaskExecution(DefaultAPITest):
    """
    Make sure tasks can't be executed after they are completed.
    When two users open the same task and both try to complete the
    task, only the first one should succeed. The second one should
    500.
    """

    def test_generic_task(self):
        case = self.get_case()
        case.run_steps(
            *test_create_debrief.get_steps(
                violation=Violation.ADDITIONAL_RESEARCH_REQUIRED
            ),
            ValidateOpenTasks(test_afwachten_intern_onderzoek),
        )

        open_tasks = self.client.get_case_tasks(case.data["id"])
        tasks = list(
            task
            for task in open_tasks
            if task["task_name"] == test_afwachten_intern_onderzoek.get_task_name()
        )

        post_data = {
            "case": case.data["id"],
            "variables": {},
            "case_user_task_id": tasks[0]["case_user_task_id"],
        }

        self.client.call(
            "post",
            f"/{GenericUserTask.endpoint}/",
            post_data,
            task_name=test_afwachten_intern_onderzoek.get_task_name(),
        )
        with self.assertRaisesRegex(Exception, "status: 500"):
            self.client.call(
                "post",
                f"/{GenericUserTask.endpoint}/",
                post_data,
                task_name=test_afwachten_intern_onderzoek.get_task_name(),
            )

    def test_non_generic_user_task(self):
        self.skipTest(
            "It should not be possible to re-execute the same task. Please note the bug might not only be about the visit endpoint. It should never be possible to re-execute a non-generic or a generic user tasks. Please not only fix this for Visit."
        )
        case = self.get_case()
        case.run_steps(
            *test_inplannen_status.get_steps(),
            ValidateOpenTasks(test_doorgeven_status_top),
        )

        post_data = {
            "case": case.data["id"],
            "authors": [],
            "start_time": str(datetime.datetime.now()),
            "situation": Situations.ACCESS_GRANTED,
            "can_next_visit_go_ahead": False,
            "top_visit_id": 42,
            "completed": True,
        }

        self.client.call(
            "post",
            f"/{test_doorgeven_status_top.endpoint}/",
            post_data,
            task_name=test_doorgeven_status_top.get_task_name(),
        )
        with self.assertRaisesRegex(Exception, "status: 500"):
            self.client.call(
                "post",
                f"/{test_doorgeven_status_top.endpoint}/",
                post_data,
                task_name=test_doorgeven_status_top.get_task_name(),
            )

    def test_non_generic_user_task_non_visit(self):
        self.skipTest("not implemented yet")
