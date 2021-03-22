import logging

from apps.schedules.models import Schedule
from apps.schedules.serializers import ScheduleSerializer
from apps.users.auth_apps import TopKeyAuth
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class ScheduleViewSet(ModelViewSet):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = ScheduleSerializer
    queryset = Schedule.objects.all()
