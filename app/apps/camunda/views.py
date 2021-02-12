from apps.camunda.models import GenericCompletedTask
from apps.camunda.serializers import (
    CamundaStateWorkerSerializer,
    CamundaTaskCompleteSerializer,
    CamundaTaskSerializer,
)
from apps.camunda.services import CamundaService
from apps.cases.models import Case
from apps.users.auth_apps import CamundaKeyAuth
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class CamundaWorkerViewSet(viewsets.ViewSet):
    """
    This is a view which can be be request from the Camunda workflow.
    """

    permission_classes = [IsInAuthorizedRealm | CamundaKeyAuth]
    serializer_class = CamundaStateWorkerSerializer

    @extend_schema(
        description="A Camunda worker POC",
        responses={200: None},
    )
    @action(
        detail=False,
        url_path="state",
        methods=["post"],
        serializer_class=CamundaStateWorkerSerializer,
    )
    def state(self, request):
        serializer = CamundaStateWorkerSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_201_CREATED)


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
        serializer = CamundaTaskCompleteSerializer(data=request.data)

        if serializer.is_valid():
            case_id = serializer.data["case"]
            case = Case.objects.get(id=case_id)
            task_id = serializer.data["camunda_task_id"]
            variables = serializer.data["variables"]
            author = request.user
            task = CamundaService().get_task(task_id)
            task_name = task["name"]

            completed_task = CamundaService().complete_task(task_id, variables)

            if completed_task:
                GenericCompletedTask.objects.create(
                    case=case,
                    description=task_name,
                    state=case.get_current_state(),
                    author=author,
                )
                return Response(
                    f"Task {serializer.data['camunda_task_id']} has been completed"
                )
            else:
                return Response(
                    "Camunda service is offline",
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        return Response(status=status.HTTP_400_BAD_REQUEST)
