import logging

from apps.camunda.models import GenericCompletedTask
from apps.camunda.serializers import (
    CamundaDateUpdateSerializer,
    CamundaEndStateWorkerSerializer,
    CamundaMessageForProcessInstanceSerializer,
    CamundaMessagerSerializer,
    CamundaProcessSerializer,
    CamundaStateWorkerSerializer,
    CamundaTaskCompleteSerializer,
    CamundaTaskListSerializer,
    CamundaTaskSerializer,
)
from apps.camunda.services import CamundaService
from apps.cases.models import Case, CaseProcessInstance
from apps.users.permissions import (
    rest_permission_classes_for_camunda,
    rest_permission_classes_for_top,
)
from apps.workflow.models import Task, Workflow
from apps.workflow.serializers import TaskListSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
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

    permission_classes = rest_permission_classes_for_camunda()
    serializer_class = CamundaStateWorkerSerializer
    queryset = GenericCompletedTask.objects.all()

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

            try:
                case = Case.objects.get(id=case_identification)
            except Case.DoesNotExist:
                return Response(
                    data="Camunda process has not started. Case does not exist",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            case_process_instance = CaseProcessInstance.objects.create(case=case)
            case_process_id = case_process_instance.process_id.__str__()

            raw_response = CamundaService().send_message(
                message_name=message_name,
                case_identification=case_identification,
                case_process_id=case_process_id,
                message_process_variables=process_variables,
            )

            if raw_response.ok:
                response = raw_response.json()[0]
                camunda_id = response["processInstance"]["id"]

                case = Case.objects.get(id=case_identification)
                case.add_camunda_id(camunda_id)
                case_process_instance.camunda_process_id = camunda_id
                case.save()
                case_process_instance.save()

                logger.info(f"Message send {message_name} ended succesfully")
                return Response(status=status.HTTP_200_OK)

            rendered_content = raw_response.content.decode("UTF-8")
            logger.error(f"FAIL: Message send response:{rendered_content}")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error(f"FAIL: Message send {serializer.errors}")
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="A Camunda service task for trigger event inside of process instance based on message",
        responses={200: None},
    )
    @action(
        detail=False,
        url_path="send-message-inside-process",
        methods=["post"],
        serializer_class=CamundaMessageForProcessInstanceSerializer,
    )
    def send_message_inside_of_process(self, request):
        logger.info("Sending message based on Camunda message to process instance")
        serializer = CamundaMessageForProcessInstanceSerializer(data=request.data)

        if serializer.is_valid():
            raw_response = CamundaService().send_message_to_process_instance(
                message_name=serializer.validated_data["message_name"],
                process_instance_id=serializer.validated_data["camunda_process_id"],
            )

            if raw_response.ok:
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        else:
            logger.error(f"FAIL: Message send {serializer.errors}")
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)


class CamundaTaskViewSet(viewsets.ViewSet):
    serializer_class = CamundaTaskCompleteSerializer
    queryset = GenericCompletedTask.objects.all()

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

            variables = data.get("variables", {})
            data["variables"] = variables
            task = Task.objects.filter(id=data["camunda_task_id"]).first()
            data.update({"description": task.name if task else "Algemene taak"})
            GenericCompletedTask.objects.create(**data)

            Workflow.complete_user_task(data["camunda_task_id"], variables)

            # camunda_response = CamundaService().complete_task(task_id, variables)

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
    permission_classes = rest_permission_classes_for_top()
    serializer_class = TaskListSerializer
    queryset = Case.objects.all()

    def get_serializer_class(self, *args, **kwargs):
        return self.serializer_class

    @extend_schema(
        parameters=[
            role_parameter,
        ],
        description="Task filter query parameters",
        responses={200: TaskListSerializer(many=True)},
    )
    def list(self, request):
        request.GET.get(role_parameter.name)

        tasks = Task.objects.filter(completed=False)
        serializer = TaskListSerializer(tasks, many=True)

        return Response(serializer.data)
