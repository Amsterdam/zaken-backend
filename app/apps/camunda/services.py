import json

import requests
from django.conf import settings


class CamundaService:
    def get_process_definitions():
        processes = []
        request_url = settings.CAMUNDA_REST_URL + "process-definition"
        response = requests.get(
            request_url, headers={"content-type": "application/json"}
        )

        content = response.json()

        for process in content:
            processes.append(process)

        return processes

    def start_instance(process=settings.CAMUNDA_PROCESS_VAKANTIE_VERHUUR):
        """
        TODO: Use bussiness key instead of process key
        """
        request_url = (
            settings.CAMUNDA_REST_URL + f"process-definition/key/{process}/start"
        )
        response = requests.post(
            request_url, headers={"content-type": "application/json"}
        )

        content = response.json()

        print(content)

        return content["id"]

    def get_all_tasks_by_instance_id(process_instance_id):
        request_url = (
            settings.CAMUNDA_REST_URL + f"task?processInstanceId={process_instance_id}"
        )
        response = requests.get(
            request_url, headers={"content-type": "application/json"}
        )

        content = response.json()
        return content

    def get_task_form_variables(task_id):
        request_url = settings.CAMUNDA_REST_URL + f"task/{task_id}/form-variables"

        response = requests.post(
            request_url, headers={"content-type": "application/json"}
        )

        content = response.json()
        return content

    def get_task_form_rendered(task_id):
        request_url = settings.CAMUNDA_REST_URL + f"task/{task_id}/rendered-form"
        response = requests.get(request_url)

        return response.content.decode("utf-8").replace("\n", "")

    def submit_form_json(task_id, form_values):
        """
        https://docs.camunda.org/manual/7.5/reference/rest/task/post-submit-form/#request
        """
        request_url = settings.CAMUNDA_REST_URL + f"task/{task_id}/submit-form"
        request_body = json.dumps({"variables": form_values})

        response = requests.post(
            request_url, data=request_body, headers={"content-type": "application/json"}
        )

        if response.ok:
            return True
        return False

    def complete_task(task_id, variables={}):
        request_url = settings.CAMUNDA_REST_URL + f"task/{task_id}/complete"
        request_body = json.dumps({"variables": variables})

        response = requests.post(
            request_url, data=request_body, headers={"content-type": "application/json"}
        )

        if response.ok:
            return True
        return False

    def send_message(message_name, message_process_variables):
        request_url = settings.CAMUNDA_REST_URL + "message"
        request_body = json.dumps(
            {"messageName": message_name, "processVariables": message_process_variables}
        )

        response = requests.post(
            request_url, data=request_body, headers={"content-type": "application/json"}
        )

        if response.ok:
            return True
        return False
