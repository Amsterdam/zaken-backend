import logging

from apps.camunda.models import GenericCompletedTask
from apps.camunda.serializers import (
    CamundaDateUpdateSerializer,
    CamundaEndStateWorkerSerializer,
    CamundaStateWorkerSerializer,
    CamundaTaskCompleteSerializer,
    CamundaTaskSerializer,
)
from apps.camunda.services import CamundaService
from apps.cases.models import Case, CaseState
from apps.users.auth_apps import CamundaKeyAuth
from django.db import transaction
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

            service = CamundaService()
            task_id = data["camunda_task_id"]

            # Task data can't be retrieved after it's been completed, so make sure to retrieve it first.
            task = service.get_task(task_id)
            task_variables = service.get_task_variables(task_id)

            try:
                state_identification = task_variables["state_identification"]["value"]
                state = CaseState.objects.get(id=state_identification)
            except (KeyError, TypeError):
                logger.error(
                    "State identification could not be retrieved from task variables. Completing task without state."
                )
                state = None

            # Boolean values should be converted to string values #ThanksCamunda
            variables = data.get("variables", {})

            for key in variables.keys():
                if "value" in variables[key]:
                    if variables[key]["value"] is True:
                        variables[key]["value"] = "true"
                    elif variables[key]["value"] is False:
                        variables[key]["value"] = "false"

            task_completed = CamundaService().complete_task(
                data["camunda_task_id"], variables
            )

            if task_completed:
                GenericCompletedTask.objects.create(
                    author=data["author"],
                    case=data["case"],
                    state=state,
                    description=task["name"],
                    variables=variables,
                )

                return Response(f"Task {data['camunda_task_id']} has been completed")
            else:
                return Response(
                    "Camunda service is offline",
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

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
