import logging

from apps.camunda.models import GenericCompletedTask
from apps.camunda.serializers import (
    CamundaDateUpdateSerializer,
    CamundaEndStateWorkerSerializer,
    CamundaMessagerSerializer,
    CamundaProcessSerializer,
    CamundaStateWorkerSerializer,
    CamundaTaskCompleteSerializer,
    CamundaTaskListSerializer,
    CamundaTaskSerializer,
)
from apps.camunda.services import CamundaService
from apps.cases.models import Case
from apps.users.auth_apps import CamundaKeyAuth, TopKeyAuth
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)

role_parameter = OpenApiParameter(
    name="role",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Role",
)


class CamundaWorkerViewSet(viewsets.ViewSet):
    """
    This is a view which can be be request from the Camunda workflow.
    """

    permission_classes = [IsInAuthorizedRealm | CamundaKeyAuth]
    serializer_class = CamundaStateWorkerSerializer

    @extend_schema(
        description="A Camunda service task for setting state",
        responses={200: None},
    )
    @action(
        detail=False,
        url_path="state",
        methods=["post"],
        serializer_class=CamundaStateWorkerSerializer,
    )
    def state(self, request):
        logger.info("Starting Camunda service task for setting state")
        logger.info(request.body)
        serializer = CamundaStateWorkerSerializer(data=request.data)

        if serializer.is_valid():
            state = serializer.save()
            logger.info("State set succesfully")
            return Response(data=state.id, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"State could not be set: {serializer.errors}")
            logger.info(serializer.errors)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="A Camunda service task for ending a state",
        responses={200: None},
    )
    @action(
        detail=False,
        url_path="end-state",
        methods=["post"],
        serializer_class=CamundaEndStateWorkerSerializer,
    )
    def end_state(self, request):
        logger.info("Starting Camunda service task for ending state")
        serializer = CamundaEndStateWorkerSerializer(data=request.data)

        if serializer.is_valid():
            state = serializer.validated_data["state_identification"]
            state.end_state()
            state.save()
            logger.info("State ended succesfully")
            return Response(status=status.HTTP_200_OK)
        else:
            logger.error(f"State could not be ended: {serializer.errors}")
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="A Camunda service task for starting process based on message",
        responses={200: None},
    )
    @action(
        detail=False,
        url_path="send-message-start-process",
        methods=["post"],
        serializer_class=CamundaMessagerSerializer,
    )
    def send_message(self, request):
        logger.info("Sending message based on Camunda message end event")
        serializer = CamundaMessagerSerializer(data=request.data)

        if serializer.is_valid():
            message_name = serializer.validated_data["message_name"]
            case_identification = serializer.validated_data["case_identification"]

            if serializer.validated_data["process_variables"]:
                process_variables = serializer.validated_data["process_variables"]
            else:
                process_variables = {}

            process_variables["endpoint"] = {"value": settings.ZAKEN_CONTAINER_HOST}
            process_variables["zaken_access_token"] = {
                "value": settings.CAMUNDA_SECRET_KEY
            }
            process_variables["case_identification"] = {
                "value": str(case_identification)
            }

            raw_response = CamundaService().send_message(
                message_name=message_name, message_process_variables=process_variables
            )

            if raw_response.ok:
                response = raw_response.json()[0]
                camunda_id = response["processInstance"]["id"]

                case = Case.objects.get(id=case_identification)
                case.add_camunda_id(camunda_id)
                case.save()

                logger.info(f"Message send {message_name} ended succesfully")
                return Response(status=status.HTTP_200_OK)

            rendered_content = raw_response.content.decode("UTF-8")
            logger.error(f"FAIL: Message send response:{rendered_content}")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error(f"FAIL: Message send {serializer.errors}")
            return Response(status=status.HTTP_400_BAD_REQUEST)


class CamundaTaskViewSet(viewsets.ViewSet):
    permission_classes = [
        IsInAuthorizedRealm,
    ]
    serializer_class = CamundaTaskCompleteSerializer

    @extend_schema(
        description="Complete a task in Camunda",
        responses={200: None},
    )
    @action(
        detail=False,
        url_path="complete",
        methods=["post"],
        serializer_class=CamundaTaskCompleteSerializer,
    )
    def complete_task(self, request):
        context = {"request": self.request}
        serializer = CamundaTaskCompleteSerializer(data=request.data, context=context)

        if serializer.is_valid():
            data = serializer.validated_data

            # Task data can't be retrieved after it's been completed, so make sure to retrieve it first.
            task_id = data["camunda_task_id"]
            task = CamundaService().get_task(task_id)

            variables = data.get("variables", {})

            # Get original structured task form from cache
            original_camunda_task_form = CamundaService._get_task_form_cache(
                CamundaService._get_task_form_cache_key(task_id)
            )
            form_dict = dict((t.get("name"), t) for t in original_camunda_task_form)

            for key, value in variables.items():
                # Only for selects, include original readable value from options
                value["value_verbose"] = (
                    dict(
                        (o.get("value"), o.get("label"))
                        for o in form_dict.get(key).get("options", [])
                    ).get(value["value"])
                    if form_dict.get(key).get("options", [])
                    else value["value"]
                )
                # Include original label
                value["label"] = form_dict.get(key, {}).get("label")

            data["variables"] = variables
            data["description"] = task["name"]

            GenericCompletedTask.objects.create(**data)

            return Response(f"Task {data['camunda_task_id']} has been completed")

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        url_path="date",
        methods=["post"],
        serializer_class=CamundaDateUpdateSerializer,
    )
    def update_due_date(self, request):
        serializer = CamundaDateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            response = CamundaService().update_due_date_task(
                data["camunda_task_id"], data["date"]
            )

            if response:
                return Response(status=status.HTTP_200_OK)

            return Response(
                "Camunda service is offline",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(status=status.HTTP_400_BAD_REQUEST)


class TaskViewSet(viewsets.ViewSet):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = CamundaTaskListSerializer

    def get_serializer_class(self, *args, **kwargs):
        return self.serializer_class

    @extend_schema(
        parameters=[
            role_parameter,
        ],
        description="Task filter query parameters",
        responses={200: CamundaTaskListSerializer(many=True)},
    )
    def list(self, request):
        role = request.GET.get(role_parameter.name)
        tasks = CamundaService().get_tasks_by_role(role)

        # Camunda tasks can be an empty list or boolean. TODO: This should just be one datatype
        if tasks is False:
            return Response(
                "Camunda service is offline",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        else:
            result = []
            for task in tasks:
                try:
                    task["case"] = Case.objects.get(
                        camunda_ids__contains=[task["processInstanceId"]]
                    )
                    result.append(task)
                except Case.DoesNotExist:
                    print(
                        f'Dropping task {task["processInstanceId"]} as the case cannot be found.'
                    )

            serializer = CamundaTaskListSerializer(result, many=True)

            return Response(serializer.data)
