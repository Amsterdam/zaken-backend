import logging

from apps.decisions.models import Decision, DecisionType
from apps.decisions.serializers import (
    DecisionSanctionSerializer,
    DecisionSerializer,
    DecisionTypeSerializer,
)
from apps.main.pagination import LimitedOffsetPaginator
from apps.users.permissions import CanPerformTask, rest_permission_classes_for_top
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .task_completion import update_decision_with_summon

logger = logging.getLogger(__name__)


class DecisionViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = DecisionSerializer
    queryset = Decision.objects.all()
    filter_backends = [DjangoFilterBackend]
    paginator_class = LimitedOffsetPaginator
    filterset_fields = {
        "case": [
            "exact",
        ],
        "date_added": ["gte", "lte", "exact", "gt", "lt"],
    }

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanPerformTask)
        return super(DecisionViewSet, self).get_permissions()

    @extend_schema(
        description="Get desicions with sanctions",
        responses={status.HTTP_200_OK: DecisionSanctionSerializer(many=True)},
    )
    @action(
        detail=False,
        url_path="sanctions",
        methods=["get"],
        serializer_class=DecisionSanctionSerializer,
    )
    def get_desicions_with_sanction(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = DecisionSanctionSerializer(
            queryset.filter(
                sanction_id__isnull=False,
                sanction_amount__isnull=False,
            ),
            many=True,
        )
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            update_decision_with_summon(serializer)
            return Response(
                data="Decision added",
                status=status.HTTP_200_OK,
            )


class DecisionTypeViewSet(GenericViewSet, ListModelMixin):
    serializer_class = DecisionTypeSerializer
    queryset = DecisionType.objects.all()
