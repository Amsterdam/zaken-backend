from apps.camunda.serializers import CamundaTaskCompleteSerializer
from apps.camunda.services import CamundaService
from apps.users.auth_apps import TopKeyAuth
from django.shortcuts import render
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class CamundaTaskViewSet(viewsets.ViewSet):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = CamundaTaskCompleteSerializer

    @action(
        detail=False,
        url_path="task/complete",
        methods=["post"],
        serializer_class=CamundaTaskCompleteSerializer,
    )
    def complete_task(self, request):
        serializer = CamundaTaskCompleteSerializer(data=request.data)

        if serializer.is_valid():
            camunda_response = CamundaService().complete_task(
                serializer.data["task_id"], serializer.data["variables"]
            )

            if camunda_response:
                return Response(f"Task {serializer.data['task_id']} has been completed")
            else:
                return Response(
                    "Camunda service is offline",
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        return Response(status=status.HTTP_400_BAD_REQUEST)
