import logging
import time

import requests

logger = logging.getLogger("api")


class API:
    headers = None

    def __init__(self, host):
        self.host = host
        token = self.call("post", "/oidc-authenticate/", json={"code": "string"})[
            "access"
        ]
        self.headers = {"Authorization": f"Bearer {token}"}

    def call(self, verb, url, json=None):
        res = requests.request(
            verb, url=f"{self.host}{url}", headers=self.headers, json=json
        )
        if not res.ok:
            logger.info(res.text)
            raise Exception(f"Error: status: {res.status_code} on url: {url}")
        return res.json()

    def get_tasks_for_case_id(self, id):
        tasks = self.call("get", f"/cases/{id}/tasks/")
        return [] if len(tasks) == 0 else tasks[0]["tasks"]


class Flow:
    def __init__(self, name, steps):
        self.name = name
        self.steps = steps
        self.case = None

    def run(self, api):
        for step in self.steps:
            if step.__class__ == CreateCase:
                self.case = step.run(api)
            elif self.case:
                step.run(api, self.case)
            else:
                raise Exception("Case not created yet")

            time.sleep(0.1)
        return self.case


class NoMoreTasks:
    def run(self, api, case):
        if len(api.get_tasks_for_case_id(case["id"])) != 0:
            raise Exception(f"Still tasks available for case id:{case['id']}")


class CreateCase:
    def __init__(self, post_data):
        self.post_data = post_data

    def run(self, api):
        return api.call("post", "/cases/", self.post_data)


class AbstractUserTask:
    endpoint = "camunda/task/complete"

    def __init__(self, id, **post_data):
        self.id = id
        self.post_data = post_data

    def run(self, api, case):
        open_tasks = api.get_tasks_for_case_id(case["id"])
        tasks = list(task for task in open_tasks if task["task_name_id"] == self.id)

        if len(tasks) == 0:
            raise Exception(f"No task found for task_name_id = {self.id}")
        if len(tasks) > 1:
            raise Exception("More then one task found")

        post_data = self.post_data | self.get_post_data(case, tasks[0])
        api.call("post", f"/{self.endpoint}/", post_data)

    def get_post_data(self, case, task):
        raise NotImplementedError


class UserTask(AbstractUserTask):
    def __init__(self, id, variables={}, **post_data):
        data = post_data | {"variables": variables}
        super(UserTask, self).__init__(id, **data)

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
            "camunda_task_id": task["camunda_task_id"],
        }


class VisitUserTask(AbstractUserTask):
    endpoint = "visits"

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
        }


class ScheduleUserTask(AbstractUserTask):
    endpoint = "schedules"

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
            "camunda_task_id": task["camunda_task_id"],
        }


class DebriefUserTask(AbstractUserTask):
    endpoint = "debriefings"

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
            "camunda_task_id": task["camunda_task_id"],
        }


class CloseCaseTask(AbstractUserTask):
    endpoint = "case-close"

    def get_post_data(self, case, task):

        return {
            "case": case["id"],
            "theme": case["theme"],
            "camunda_task_id": task["camunda_task_id"],
        }
