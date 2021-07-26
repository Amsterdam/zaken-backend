import logging

from apps.schedules.models import Schedule
from apps.schedules.serializers import ScheduleCreateSerializer
from apps.users.permissions import rest_permission_classes_for_top
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class ScheduleViewSet(GenericViewSet, CreateModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = ScheduleCreateSerializer
    queryset = Schedule.objects.all()
