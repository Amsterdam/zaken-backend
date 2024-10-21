import logging

from apps.main.pagination import LimitedOffsetPaginator
from apps.summons.models import Summon, SummonedPerson, SummonType
from apps.summons.serializers import (
    SummonedPersonAnonomizedSerializer,
    SummonSerializer,
    SummonTypeSerializer,
)
from apps.users.permissions import CanPerformTask, rest_permission_classes_for_top
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class SummonViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = SummonSerializer
    queryset = Summon.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["case"]
    pagination_class = LimitedOffsetPaginator

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanPerformTask)
        return super(SummonViewSet, self).get_permissions()


class SummonTypeViewSet(GenericViewSet, ListModelMixin):
    serializer_class = SummonTypeSerializer
    queryset = SummonType.objects.all()


class SummonedPersonViewSet(GenericViewSet, ListModelMixin):
    serializer_class = SummonedPersonAnonomizedSerializer
    queryset = SummonedPerson.objects.all()
