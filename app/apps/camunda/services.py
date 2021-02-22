import json
import logging

import requests
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class CamundaService:
    def __init__(self, rest_url=settings.CAMUNDA_REST_URL):
        self.rest_url = rest_url

    def _process_request(self, request_path, request_body=None, post=False):
        request_path = self.rest_url + request_path

        try:
            if post:
                response = requests.post(
                    request_path,
                    data=request_body,
                    headers={"content-type": "application/json"},
                )
            else:
                response = requests.get(
                    request_path,
                    data=request_body,
                    headers={"content-type": "application/json"},
                )
            return response
        except requests.exceptions.Timeout:
            response = Response(
                "Camunda service is offline",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
            response.ok = False
            return response
        except requests.exceptions.RequestException:
            response = Response(status=status.HTTP_400_BAD_REQUEST)
            response.ok = False
            return response

    def get_process_definitions(self):
        processes = []
        response = self._process_request("/process-definition")

        if response.ok:
            content = response.json()

            for process in content:
                processes.append(process)
            return processes
        else:
            return False

    def start_instance(
        self, case_identification, process=settings.CAMUNDA_PROCESS_VAKANTIE_VERHUUR
    ):
        """
        TODO: Use business key instead of process key
        """
        request_path = f"/process-definition/key/{process}/start"
        request_body = json.dumps(
            {
                "variables": {
                    "zaken_access_token": {
                        "value": settings.CAMUNDA_SECRET_KEY,
                        "type": "String",
                    },
                    "zaken_state_endpoint": {
                        "value": f'{settings.ZAKEN_CONTAINER_HOST}{reverse("camunda-workers-state")}',
                        "type": "String",
                    },
                    "zaken_end_state_endpoint": {
                        "value": f'{settings.ZAKEN_CONTAINER_HOST}{reverse("camunda-workers-end-state")}',
                        "type": "String",
                    },
                    "case_identification": {
                        "value": case_identification,
                        "type": "String",
                    },
                },
            }
        )
        logger.info("Starting camunda process instance")

        response = self._process_request(
            request_path, request_body=request_body, post=True
        )

        if response.ok:
            content = response.json()
            return content["id"]
        else:
            return False

    def get_all_tasks_by_instance_id(self, process_instance_id):
        request_path = f"/task?processInstanceId={process_instance_id}"
        response = self._process_request(request_path)

        if response.ok:
            task_list = response.json()

            for index, task in enumerate(task_list):
                roles = []
                task_roles = self.get_task_user_role(task["id"])

                for role in task_roles:
                    roles.append(role["groupId"])

                role_dict = {"roles": roles}
                task_list[index].update(role_dict)

            return task_list
        else:
            return False

    def get_task(self, task_id):
        response = self._process_request(f"/task/{task_id}")
        if response.ok:
            return response.json()
        else:
            return False

    def get_task_variables(self, task_id):
        response = self._process_request(f"/task/{task_id}/variables")
        if response.ok:
            return response.json()
        else:
            return False

    def get_task_by_task_name_id_and_camunda_id(self, task_name_id, camunda_id):
        response = self._process_request(
            f"/task/?taskDefinitionKey={task_name_id}&processInstanceId={camunda_id}"
        )
        task_list = json.loads(response.content)

        if len(task_list) > 0:
            return task_list[0]
        else:
            return False

    def get_task_user_role(self, camunda_task_id):
        response = self._process_request(f"/task/{camunda_task_id}/identity-links")

        if response.ok:
            content = response.json()
            return content
        else:
            return False

    def get_task_form_variables(self, camunda_task_id):
        response = self._process_request(f"/task/{camunda_task_id}/form-variables")

        if response.ok:
            content = response.json()
            return content
        else:
            return False

    def get_task_form_rendered(self, camunda_task_id):
        """
        TODO: probably not needed but could be nice refrence
        """
        request_path = f"/task/{camunda_task_id}/rendered-form"
        response = self._process_request(request_path)

        return response.content.decode("utf-8").replace("\n", "")

    def submit_form_json(self, camunda_task_id, form_values):
        """
        https://docs.camunda.org/manual/7.5/reference/rest/task/post-submit-form/#request
        """
        request_path = f"/task/{camunda_task_id}/submit-form"
        request_body = json.dumps({"variables": form_values})

        response = self._process_request(request_path, request_body, post=True)

        return response

    def complete_task(self, camunda_task_id, variables={}):
        request_path = f"/task/{camunda_task_id}/complete"
        request_body = json.dumps({"variables": variables})

        response = self._process_request(request_path, request_body, post=True)

        return response

    def send_message(self, message_name, message_process_variables):
        request_body = json.dumps(
            {"messageName": message_name, "processVariables": message_process_variables}
        )
        response = self._process_request("/message", request_body, post=True)

        return response
