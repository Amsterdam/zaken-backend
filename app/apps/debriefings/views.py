import logging

from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import (
    DebriefingCreateSerializer,
    DebriefingSerializer,
)
from apps.users.permissions import CanPerformTask, rest_permission_classes_for_top
from rest_framework import status
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .task_completion import complete_task_create_debrief

logger = logging.getLogger(__name__)


class DebriefingViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = DebriefingSerializer
    queryset = Debriefing.objects.all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DebriefingCreateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanPerformTask)
        return super(DebriefingViewSet, self).get_permissions()

    def create(self, request):
        serializer = DebriefingCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            complete_task_create_debrief(serializer)
            return Response(
                data="Debrief added",
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
