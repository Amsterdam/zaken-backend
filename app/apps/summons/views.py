import logging

from apps.summons.models import Summon
from apps.summons.serializers import SummonSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import ViewSet

logger = logging.getLogger(__name__)


class SummonViewSet(ViewSet, CreateModelMixin):
    serializer_class = SummonSerializer
    queryset = Summon.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["case"]
