import logging

from apps.summons.models import Summon
from apps.summons.serializers import SummonSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class SummonViewSet(ModelViewSet):
    serializer_class = SummonSerializer
    queryset = Summon.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["case"]
