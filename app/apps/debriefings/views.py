import logging

from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import (
    DebriefingCreateSerializer,
    ViolationTypeSerializer,
)
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class DebriefingViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    serializer_class = DebriefingCreateSerializer
    queryset = Debriefing.objects.all()

    @extend_schema(
        description="Gets the ViolationTypes",
        responses={status.HTTP_200_OK: ViolationTypeSerializer(many=True)},
    )
    @action(
        detail=False,
        url_path="violation-types",
        methods=["get"],
    )
    def violation_types(self, request):
        paginator = PageNumberPagination()
        types = [
            {"key": t[0]}
            for t in Debriefing.VIOLATION_CHOICES
            if t[0] != Debriefing.VIOLATION_AUTHORIZATION_REQUEST
        ]
        context = paginator.paginate_queryset(types, request)
        serializer = ViolationTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)
