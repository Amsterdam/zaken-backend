import logging

from .tasks import AbstractUserTask

logger = logging.getLogger("api")


class Validator:
    tasks = []

    def is_async(self):
        return bool(filter(lambda task: task.is_async(), self.tasks))


class ValidateEvents(Validator):
    def __init__(self, events: list):
        self.events = events

    def run(self, api, case):
        # Get the task names we want to check
        assert_names = list(map(lambda task: task.task_name, self.tasks))
        assert_names.sort()

        # Get the names of all open tasks
        open_tasks = api.get_case_tasks(case.data["id"])
        open_task_names = api.get_names_from_tasks(open_tasks)
        open_task_names.sort()

        logger.info(f"Expecting {assert_names} == {open_task_names}")
        if assert_names != open_task_names:
            raise Exception(
                f"Expected {assert_names}, found {open_task_names}. Case id:{case.data['id']}"
            )


class ValidateOpenTasks(Validator):
    def __init__(self, tasks: list[AbstractUserTask]):
        self.tasks = filter(lambda task: task is not None, tasks)

    def run(self, api, case):
        # Get the task names we want to check
        assert_names = list(map(lambda task: task.task_name, self.tasks))
        assert_names.sort()

        # Get the names of all open tasks
        open_tasks = api.get_case_tasks(case.data["id"])
        open_task_names = api.get_names_from_tasks(open_tasks)
        open_task_names.sort()

        logger.info(f"Expecting {assert_names} == {open_task_names}")
        if assert_names != open_task_names:
            raise Exception(
                f"Expected {assert_names}, found {open_task_names}. Case id:{case.data['id']}"
            )


class ValidateNumberOfOpenTasks(Validator):
    def __init__(self, count):
        self.count = count

    def run(self, api, case):
        tasks = api.get_case_tasks(case.data["id"])
        num_open_tasks = len(tasks)
        if num_open_tasks != self.count:
            raise Exception(
                f"{self.count} open tasks expected, found {api.get_names_from_tasks(tasks)}. Case id:{case.data['id']}"
            )
