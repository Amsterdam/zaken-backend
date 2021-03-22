import logging

from apps.decisions.models import Decision
from apps.decisions.serializers import DecisionSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class DecisionViewSet(ModelViewSet):
    serializer_class = DecisionSerializer
    queryset = Decision.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["case"]
