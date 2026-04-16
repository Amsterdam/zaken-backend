import logging

from apps.schedules.models import Action, DaySegment, Priority, Schedule, WeekSegment
from apps.schedules.serializers import (
    ActionSerializer,
    DaySegmentSerializer,
    PrioritySerializer,
    ScheduleCreateSerializer,
    SchedulePriorityUpdateSerializer,
    WeekSegmentSerializer,
)
from apps.users.permissions import CanPerformTask, rest_permission_classes_for_top
from apps.workflow.models import CaseWorkflow
from rest_framework.mixins import CreateModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class ScheduleViewSet(
    GenericViewSet, CreateModelMixin, ListModelMixin, UpdateModelMixin
):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = ScheduleCreateSerializer
    queryset = Schedule.objects.all()
    http_method_names = ["get", "patch", "post"]

    def get_permissions(self):
        permission_classes = list(self.permission_classes)

        if self.request.method not in SAFE_METHODS:
            permission_classes.append(CanPerformTask)

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "partial_update":
            return SchedulePriorityUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        case = serializer.validated_data.get("case")

        # Check if this is a schedule for an additional visit
        is_additional = False
        if case:
            workflow = CaseWorkflow.objects.filter(case=case).first()
            if (
                workflow
                and workflow.case_state_type
                and "aanvullend" in workflow.case_state_type.name.lower()
            ):
                is_additional = True

        serializer.save(is_additional=is_additional)


class ActionViewSet(GenericViewSet, ListModelMixin):
    serializer_class = ActionSerializer
    queryset = Action.objects.all()


class WeekSegmentViewSet(GenericViewSet, ListModelMixin):
    serializer_class = WeekSegmentSerializer
    queryset = WeekSegment.objects.all()


class DaySegmentViewSet(GenericViewSet, ListModelMixin):
    serializer_class = DaySegmentSerializer
    queryset = DaySegment.objects.all()


class PriorityViewSet(GenericViewSet, ListModelMixin):
    serializer_class = PrioritySerializer
    queryset = Priority.objects.all()
