import datetime
import logging

from api.config import Situations, Violation
from api.tasks import GenericUserTask
from api.tasks.debrief import Debrief, WaitInternalResearch
from api.tasks.visit import ScheduleVisit, Visit
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks

logger = logging.getLogger("api")


class TestDuplicateTaskExecution(DefaultAPITest):
    """
    Make sure tasks can't be executed after they are completed.
    When two users open the same task and both try to complete the
    task, only the first one should succeed. The second one should
    500.
    """

    def test_generic_task(self):
        self.skipTest(
            "It should not be possible to re-execute the same task. Please note the bug might not only be about the generic-tasks. It should never be possible to re-execute a non-generic or a generic user tasks. Please not only fix this for Generic user-tasks."
        )
        case = self.get_case()
        case.run_steps(
            *Debrief.get_steps(violation=Violation.ADDITIONAL_RESEARCH_REQUIRED),
            ValidateOpenTasks(WaitInternalResearch),
        )

        open_tasks = self.client.get_case_tasks(case.data["id"])
        tasks = list(
            task
            for task in open_tasks
            if task["task_name"] == WaitInternalResearch.task_name
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
            task_name=WaitInternalResearch.task_name,
        )
        with self.assertRaisesRegex(Exception, "status: 500"):
            self.client.call(
                "post",
                f"/{GenericUserTask.endpoint}/",
                post_data,
                task_name=WaitInternalResearch.task_name,
            )

    def test_non_generic_user_task(self):
        self.skipTest(
            "It should not be possible to re-execute the same task. Please note the bug might not only be about the visit endpoint. It should never be possible to re-execute a non-generic or a generic user tasks. Please not only fix this for Visit."
        )
        case = self.get_case()
        case.run_steps(
            *ScheduleVisit.get_steps(),
            ValidateOpenTasks(Visit),
        )

        open_tasks = self.client.get_case_tasks(case.data["id"])
        tasks = list(
            task for task in open_tasks if task["task_name"] == Visit.task_name
        )
        post_data = {
            "case": case.data["id"],
            # "case_user_task_id": tasks[0]["case_user_task_id"],
            "task": tasks[0]["case_user_task_id"],
            "authors": [],
            "start_time": str(datetime.datetime.now()),
            "situation": Situations.ACCESS_GRANTED,
            "can_next_visit_go_ahead": False,
        }

        self.client.call(
            "post",
            f"/{Visit.endpoint}/",
            post_data,
            task_name=Visit.task_name,
        )
        with self.assertRaisesRegex(Exception, "status: 500"):
            self.client.call(
                "post",
                f"/{Visit.endpoint}/",
                post_data,
                task_name=Visit.task_name,
            )
