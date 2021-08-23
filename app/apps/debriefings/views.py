import logging

from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import DebriefingCreateSerializer
from apps.users.permissions import CanPerformTask, rest_permission_classes_for_top
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class DebriefingViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = DebriefingCreateSerializer
    queryset = Debriefing.objects.all()

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanPerformTask)
        return super(DebriefingViewSet, self).get_permissions()
