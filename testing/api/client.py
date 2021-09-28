import json
import logging

import requests
from api.case import Case

logger = logging.getLogger("api")


class Client:
    authenticated = False

    def __init__(self, config):
        self.legacy_mode = config["legacy_mode"]  # using Spiff vs Camunda
        self.host = config["host"]
        if "://api.wonen.zaken.amsterdam.nl/" in self.host:
            raise Exception(f"Host ({self.host}) not allowed")

    def request(self, verb, url, headers=None, json=None):
        url = f"{self.host}{url}"
        logger.info(f"Request ({verb}) api on '{url}' with json:\n{json}\n\n")

        res = requests.request(verb, url=url, headers=headers, json=json)
        logger.info(f"Response api status:{res.status_code} with text:\n{res.text}\n\n")

        if not res.ok:
            logger.info(res.text)
            raise Exception(f"Error: status: {res.status_code} on url: {url}")

        return res.json()

    def call(self, verb, url, json=None):
        if not self.authenticated:
            response = self.request(
                "post", "/oidc-authenticate/", json={"code": "string"}
            )
            self.headers = {"Authorization": f"Bearer {response['access']}"}
            self.authenticated = True
        return self.request(verb, url, headers=self.headers, json=json)

    def get_case_tasks(self, case_id):
        response = self.call("get", f"/cases/{case_id}/tasks/")
        tasks = [] if len(response) == 0 else response[0]["tasks"]

        logging.info(f"Open tasks for case id {case_id}:")
        logging.info(f"{json.dumps(tasks, sort_keys=True, indent=4)}\n\n")

        return tasks

    def get_close_reasons(self, theme):
        return self.call("get", f"/themes/{theme}/case-close-reasons/")["results"]

    def get_task_name(self, task):
        (name, legacy_name) = task
        return legacy_name if self.legacy_mode else name

    def create_case(self, data):
        return Case(self.call("post", "/cases/", data), self)
