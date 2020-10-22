from apps.cases.models import Case
from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import (
    DebriefingCreateSerializer,
    DebriefingCreateTempSerializer,
    DebriefingSerializer,
)
from django.shortcuts import render
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class DebriefingViewSet(
    GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    permission_classes = [IsAuthenticated]
    serializer_class = DebriefingSerializer
    queryset = Debriefing.objects.all()

    def get_serializer(self):
        if self.action == "create":
            return DebriefingCreateSerializer

        return self.serializer_class

    def create(self, request, *args, **kwargs):
        """
        The Debriefing Author is automatically linked to the currently authenticated user
        """
        user = request.user
        case_identificaton = request.data.get("case")
        case = Case.objects.get(identification=case_identificaton)

        data = {**request.data, "author": user.id, "case": case.id}

        serializer = DebriefingCreateTempSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
