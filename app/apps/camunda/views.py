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
from apps.users.permissions import (
    rest_permission_classes_for_camunda,
    rest_permission_classes_for_top,
)
from apps.workflow.models import CaseUserTask
from django.shortcuts import get_object_or_404
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
            task = get_object_or_404(CaseUserTask, id=data["case_user_task_id"])
            data.update(
                {
                    "description": task.name if task else "Algemene taak",
                    "variables": task.map_variables_on_form(variables),
                }
            )

            try:
                # camunda_response = CamundaService().complete_task(task_id, variables)
                GenericCompletedTask.objects.create(**data)
                task.workflow.complete_user_task_and_create_new_user_tasks(
                    task.task_id, variables
                )
                return Response(
                    f"CaseUserTask {data['case_user_task_id']} has been completed"
                )
            except Exception:
                return Response(
                    f"CaseUserTask {data['case_user_task_id']} has NOT been completed"
                )

        return Response(status=status.HTTP_400_BAD_REQUEST)
