import logging

from apps.quick_decisions.models import QuickDecision, QuickDecisionType
from apps.quick_decisions.serializers import (
    QuickDecisionSerializer,
    QuickDecisionTypeSerializer,
)
from apps.users.permissions import CanPerformTask, rest_permission_classes_for_top
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class QuickDecisionViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = QuickDecisionSerializer
    queryset = QuickDecision.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "case": [
            "exact",
        ],
    }

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanPerformTask)
        return super(QuickDecisionViewSet, self).get_permissions()


class QuickDecisionTypeViewSet(GenericViewSet, ListModelMixin):
    serializer_class = QuickDecisionTypeSerializer
    queryset = QuickDecisionType.objects.all()
