import logging

from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import DebriefingCreateSerializer
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import ViewSet

logger = logging.getLogger(__name__)


class DebriefingViewSet(ViewSet, CreateModelMixin):
    serializer_class = DebriefingCreateSerializer
    queryset = Debriefing.objects.all()
