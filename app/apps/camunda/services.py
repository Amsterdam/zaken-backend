import json
import logging

import requests
from django.conf import settings
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
            return Response(
                "Camunda service is offline",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except requests.exceptions.RequestException:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_process_definitions(self):
        processes = []
        response = self._process_request("/process-definition")

        try:
            response.raise_for_status()
            content = response.json()

            for process in content:
                processes.append(process)
            return processes
        except requests.exceptions.RequestException:
            return False

    def start_instance(self, process=settings.CAMUNDA_PROCESS_VAKANTIE_VERHUUR):
        """
        TODO: Use business key instead of process key
        """
        request_path = f"/process-definition/key/{process}/start"
        response = self._process_request(request_path, post=True)

        try:
            response.raise_for_status()
            content = response.json()
            return content["id"]
        except requests.exceptions.RequestException:
            return False

    def get_all_tasks_by_instance_id(self, process_instance_id):
        request_path = f"/task?processInstanceId={process_instance_id}"
        response = self._process_request(request_path)

        try:
            response.raise_for_status()
            content = response.json()
            return content
        except requests.exceptions.RequestException:
            return False

    def get_task_form_variables(self, task_id):
        response = self._process_request(f"/task/{task_id}/form-variables")

        try:
            response.raise_for_status()
            content = response.json()
            return content
        except requests.exceptions.RequestException:
            return False

    def get_task_form_rendered(self, task_id):
        request_path = f"/task/{task_id}/rendered-form"
        response = self._process_request(request_path)

        return response.content.decode("utf-8").replace("\n", "")

    def submit_form_json(self, task_id, form_values):
        """
        https://docs.camunda.org/manual/7.5/reference/rest/task/post-submit-form/#request
        """
        request_path = f"/task/{task_id}/submit-form"
        request_body = json.dumps({"variables": form_values})

        response = self._process_request(request_path, request_body, post=True)

        return response

    def complete_task(self, task_id, variables={}):
        request_path = f"/task/{task_id}/complete"
        request_body = json.dumps({"variables": variables})

        response = self._process_request(request_path, request_body, post=True)

        return response

    def send_message(self, message_name, message_process_variables):
        request_body = json.dumps(
            {"messageName": message_name, "processVariables": message_process_variables}
        )
        response = self._process_request("/message", request_body, post=True)

        return response
