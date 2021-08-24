import logging

from apps.schedules.models import Schedule
from apps.schedules.serializers import ScheduleCreateSerializer
from apps.users.permissions import CanPerformTask, rest_permission_classes_for_top
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class ScheduleViewSet(GenericViewSet, CreateModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = ScheduleCreateSerializer
    queryset = Schedule.objects.all()

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanPerformTask)
        return super(ScheduleViewSet, self).get_permissions()
