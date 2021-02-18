import logging

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

logger = logging.getLogger(__name__)


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
        logger.info(
            f"Camunda is setting state for case {request.data['case_identification']}"
        )
        print(
            f"P Camunda is setting state for case {request.data['case_identification']}"
        )

        serializer = CamundaStateWorkerSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            logger.info("State set succesfully")
            print("P State set succesfully")
            return Response(status=status.HTTP_201_CREATED)
        else:
            print(f"p State could not be set: {serializer.errors}")
            logger.info(f"State could not be set: {serializer.errors}")
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
            task = CamundaService().get_task(data["camunda_task_id"])

            task_completed = CamundaService().complete_task(
                data["camunda_task_id"], data.get("variables", {})
            )

            if task_completed:
                GenericCompletedTask.objects.create(
                    author=data["author"],
                    case=data["case"],
                    state=data["case"].get_current_state(),
                    description=task["name"],
                    variables=data.get("variables", {}),
                )

                return Response(f"Task {data['camunda_task_id']} has been completed")
            else:
                return Response(
                    "Camunda service is offline",
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        return Response(status=status.HTTP_400_BAD_REQUEST)
