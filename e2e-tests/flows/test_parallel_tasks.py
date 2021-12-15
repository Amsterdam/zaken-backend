from concurrent.futures import as_completed

from api.config import Violation
from api.events import GenericTaskEvent
from api.tasks import GenericUserTask
from api.tasks.debrief import test_verwerken_debrief
from api.tasks.summon import test_opstellen_concept_aanschrijving
from api.test import DefaultAPITest
from api.validators import ValidateOpenTasks
from requests_futures.sessions import FuturesSession


def get_post_data(case_id, task_id):
    return {"case": case_id, "case_user_task_id": task_id, "variables": {}}


class TestParallelTasks(DefaultAPITest):
    """
    Test if the service can handle multiple requests to the same case at once.
    This might seem like a rare condition given the small number of active
    users on the application. It can however help us debug the locking mechanism
    and asynchronous nature of our setup.
    """

    def test(self):
        case = self.get_case()
        case.run_steps(
            *test_verwerken_debrief.get_steps(violation=Violation.YES),
        )

        open_tasks = self.client.get_case_tasks(case.data["id"])
        session = FuturesSession()

        futures = []
        # requests all open tasks at once
        for task in open_tasks:
            json = get_post_data(case.data["id"], task["case_user_task_id"])
            future = session.post(
                f"{self.client.host}/{GenericUserTask.endpoint}/",
                json=json,
                headers=self.client.headers,
            )
            futures.append(future)

        # wait for every request to finish
        for future in as_completed(futures):
            future.result()

        # poll for the expected result
        case.run_steps(
            ValidateOpenTasks(test_opstellen_concept_aanschrijving),
            extra_events=[
                GenericTaskEvent.type,
                GenericTaskEvent.type,
                GenericTaskEvent.type,
            ],
        )
