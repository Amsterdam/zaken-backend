import logging

from apps.schedules.models import Schedule
from apps.schedules.serializers import ScheduleSerializer
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class ScheduleViewSet(ModelViewSet):
    serializer_class = ScheduleSerializer
    queryset = Schedule.objects.all()
