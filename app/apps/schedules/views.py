import logging

from apps.schedules.models import Schedule
from apps.schedules.serializers import ScheduleCreateSerializer
from apps.users.auth_apps import TopKeyAuth
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import ViewSet

logger = logging.getLogger(__name__)


class ScheduleViewSet(ViewSet, CreateModelMixin):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = ScheduleCreateSerializer
    queryset = Schedule.objects.all()
