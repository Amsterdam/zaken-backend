import logging

from api import events

logger = logging.getLogger("api")


class AbstractUserTask:
    data = None
    event = None
    task = None

    def __init__(self, **data):
        self.data = data

    def __str__(self):
        return f"<{self.__module__}.{self.__class__.__name__} task_name:{self.task_name} event:{self.event.type}>"

    def is_ready(self, client, case):
        open_tasks = client.get_case_tasks(case.data["id"])
        tasks = list(task for task in open_tasks if task["task_name"] == self.task_name)

        if len(tasks) > 1:
            raise Exception(f"More then one task found matching task {self}")

        if len(tasks) == 1:
            self.task = tasks[0]
            return True

        return False

    def run(self, client, case):
        extra = self.get_post_data(case, self.task)
        post_data = self.data | extra if self.data else extra
        client.call("post", f"/{self.endpoint}/", post_data, task_name=self.task_name)

    def get_post_data(self, case, task):
        return {
            "case": case.data["id"],
        }


class GenericUserTask(AbstractUserTask):
    endpoint = "generic-tasks/complete"
    event = events.GenericTaskEvent

    def __init__(self, **variables):
        self.variables = variables
        super(GenericUserTask, self).__init__()

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "variables": self.variables,
            "case_user_task_id": task["case_user_task_id"],
        }
