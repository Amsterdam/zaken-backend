import json
import logging

import requests
from apps.camunda.utils import get_form_details, get_forms
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class CamundaService:
    def __init__(self, rest_url=settings.CAMUNDA_REST_URL):
        self.rest_url = rest_url

    def _process_request(self, request_path, request_body=None, post=False, put=False):
        request_path = self.rest_url + request_path

        try:
            if post:
                response = requests.post(
                    request_path,
                    data=request_body,
                    headers={
                        "content-type": "application/json",
                        "API_KEY": settings.CAMUNDA_REST_AUTH,
                    },
                )
            elif put:
                response = requests.put(
                    request_path,
                    data=request_body,
                    headers={
                        "content-type": "application/json",
                        "API_KEY": settings.CAMUNDA_REST_AUTH,
                    },
                )
            else:
                response = requests.get(
                    request_path,
                    data=request_body,
                    headers={
                        "content-type": "application/json",
                        "API_KEY": settings.CAMUNDA_REST_AUTH,
                    },
                )

            logger.info(
                f"Request to Camunda succesful. Response: {response.content} from url: {request_path}"
            )
            return response
        except requests.exceptions.Timeout:
            logger.info("Request to Camunda timed out")
            response = Response(
                "Camunda service is offline",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
            response.ok = False
            return response
        except requests.exceptions.RequestException:
            logger.info("Request to Camunda threw an exception")
            response = Response(status=status.HTTP_400_BAD_REQUEST)
            response.ok = False
            return response

    def _get_form_with_task(self, camunda_task_id):
        task_list = []
        response = self._process_request(f"/task/{camunda_task_id}/form-variables")

        if response.ok:
            response_json = response.json()

            for task in response_json:
                if not response_json[task]["value"]:
                    task_list.append(response_json[task])

            return task_list
        else:
            return False

    def _get_rendered_form_with_task(self, camunda_task_id):
        request_path = f"/task/{camunda_task_id}/rendered-form"
        response = self._process_request(request_path)

        if response.ok:
            return response.content.decode("utf-8")
        return False

    def _get_task_user_role(self, camunda_task_id):
        response = self._process_request(f"/task/{camunda_task_id}/identity-links")

        if response.ok:
            content = response.json()
            return content
        else:
            return False

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
        self,
        case_identification=False,
        request_body={},
        process=settings.CAMUNDA_PROCESS_VISIT,
    ):
        """
        TODO: Use business key instead of process key
        """
        request_path = f"/process-definition/key/{process}/start"
        logger.info("Starting camunda process instance")

        response = self._process_request(
            request_path, request_body=request_body, post=True
        )

        if response.ok:
            content = response.json()
            return (content["id"], response)
        else:
            return (False, response)

    def get_all_tasks_by_instance_id(self, process_instance_id):
        request_path = f"/task?processInstanceId={process_instance_id}"
        response = self._process_request(request_path)

        if response.ok:
            task_list = response.json()

            for index, task in enumerate(task_list):
                roles = []
                task_roles = self._get_task_user_role(task["id"])
                task_form_variables = self.get_task_form_variables(task["id"])
                task_render_form = self._get_rendered_form_with_task(task["id"])
                task_json_form = self.get_task_form_rendered(task["id"])

                if task_roles:
                    for role in task_roles:
                        roles.append(role["groupId"])

                extra_info_dict = {
                    "roles": roles,
                    "form": task_json_form,
                    "render_form": task_render_form,
                    "form_variables": task_form_variables,
                }
                task_list[index].update(extra_info_dict)

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

    def get_task_form_variables(self, camunda_task_id):
        response = self._process_request(f"/task/{camunda_task_id}/form-variables")

        if response.ok:
            content = response.json()
            return content
        else:
            return False

    def get_task_form_rendered(self, camunda_task_id):
        request_path = f"/task/{camunda_task_id}/rendered-form"
        response = self._process_request(request_path)

        if response.ok:
            response_form = get_forms(response.content)
            if len(response_form) == 1:
                response_json_form = get_form_details(response_form[0])

                return response_json_form
            else:
                response = Response(status=status.HTTP_400_BAD_REQUEST)
                response.ok = False
                return response

        return False

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

    def update_due_date_task(self, camunda_task_id, date):
        task = self.get_task(camunda_task_id)
        request_path = f"/task/{camunda_task_id}/"

        # changes only due date but is needed for some f'ing reason
        request_body = json.dumps(
            {
                "name": task["name"],
                "description": task["description"],
                "priority": task["priority"],
                "assignee": task["assignee"],
                "owner": task["owner"],
                "delegationState": task["delegationState"],
                "due": date.strftime("%Y-%m-%dT%H:%M:%S.000+0200"),
                "followUp": task["followUp"],
                "parentTaskId": task["parentTaskId"],
                "caseInstanceId": task["caseInstanceId"],
                "tenantId": task["tenantId"],
            }
        )

        response = self._process_request(request_path, request_body, put=True)
        return response

    def send_message(
        self, message_name, case_identification=False, message_process_variables={}
    ):
        message_process_variables["endpoint"] = {"value": settings.ZAKEN_CONTAINER_HOST}
        message_process_variables["zaken_access_token"] = {
            "value": settings.CAMUNDA_SECRET_KEY
        }
        request_body = {
            "messageName": message_name,
            "processVariables": message_process_variables,
            "resultEnabled": True,
        }

        if case_identification:
            request_body["processVariables"]["case_identification"] = {
                "value": str(case_identification)
            }

        request_json_body = json.dumps(request_body)
        response = self._process_request("/message", request_json_body, post=True)

        return response
