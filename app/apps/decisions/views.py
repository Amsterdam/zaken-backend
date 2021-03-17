import logging

from apps.decisions.models import Decision, DecisionType
from apps.decisions.serializers import DecisionSerializer, DecisionTypeSerializer
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class DecisionViewSet(ModelViewSet):
    serializer_class = DecisionSerializer
    queryset = Decision.objects.all()
