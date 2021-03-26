import logging

from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import (
    DebriefingCreateSerializer,
    DebriefingSerializer,
)
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class DebriefingViewSet(
    GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = DebriefingSerializer
    queryset = Debriefing.objects.all()

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "create":
            return DebriefingCreateSerializer

        return self.serializer_class
