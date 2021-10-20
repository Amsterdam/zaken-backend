import logging

from api.case import Case

logger = logging.getLogger("api")


class Validator:
    tasks = []

    def is_async(self):
        return bool(filter(lambda task: task.is_async(), self.tasks))

    def run(self, client, case: Case):
        pass


class ValidateOpenTasks(Validator):
    def __init__(self, *tasks):
        self.tasks = list(map(lambda task: task.task_name, tasks))
        self.tasks.sort()

    def __str__(self):
        return f"<{self.__module__}.{self.__class__.__name__} tasks:{self.tasks}>"

    def is_ready(self, client, case: Case):
        # Get the names of all open tasks
        open_tasks = client.get_case_tasks(case.data["id"])
        open_task_names = client.get_names_from_tasks(open_tasks)
        open_task_names.sort()

        logger.info(
            f"Expecting case:{case.data['id']} to have:\n{self.tasks}\nFound:\n{open_task_names}"
        )

        return not self.is_async() or (
            self.is_async() and self.tasks == open_task_names
        )


class ValidateNoOpenTasks(ValidateOpenTasks):
    def __init__(self):
        pass
