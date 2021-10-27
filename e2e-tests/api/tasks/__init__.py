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

    def is_async(self):
        return True  # hasattr(self, "asynchronous") and self.asynchronous

    def is_ready(self, client, case):
        open_tasks = client.get_case_tasks(case.data["id"])
        tasks = list(task for task in open_tasks if task["task_name"] == self.task_name)

        if len(tasks) > 1:
            raise Exception(f"More then one task found matching task {self}")

        if len(tasks) == 1:
            self.task = tasks[0]
        elif not self.is_async():
            raise Exception(
                f"No tasks found for this sync task {self}. Looking for {self.task_name} for case {case}."
            )

        ready = not self.is_async() or (self.is_async() and self.task)
        if not ready:
            logger.info(
                f"is_ready:{ready} lookin for case {case} with task {self}, found {tasks}"
            )

        return ready

    def run(self, client, case):
        extra = self.get_post_data(case, self.task)
        post_data = self.data | extra if self.data else extra
        client.call("post", f"/{self.endpoint}/", post_data)

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
