import logging

from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import DebriefingCreateSerializer
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class DebriefingViewSet(GenericViewSet, CreateModelMixin):
    serializer_class = DebriefingCreateSerializer
    queryset = Debriefing.objects.all()
