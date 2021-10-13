import logging

from apps.camunda.models import GenericCompletedTask
from apps.camunda.serializers import CamundaTaskCompleteSerializer
from apps.workflow.models import CaseUserTask
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)


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
