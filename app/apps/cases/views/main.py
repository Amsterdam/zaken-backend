import logging

from apps.cases.models import CaseClose, CaseCloseReason, CaseCloseResult, CitizenReport
from apps.cases.serializers import (
    CaseCloseReasonSerializer,
    CaseCloseResultSerializer,
    CaseCloseSerializer,
    CitizenReportAnonomizedSerializer,
)
from apps.users.permissions import CanCloseCase, rest_permission_classes_for_top
from rest_framework import mixins, viewsets
from rest_framework.permissions import SAFE_METHODS

logger = logging.getLogger(__name__)


class CaseCloseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseCloseSerializer
    queryset = CaseClose.objects.all()

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanCloseCase)
        return super(CaseCloseViewSet, self).get_permissions()


class CaseCloseResultViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CaseCloseResultSerializer
    queryset = CaseCloseResult.objects.all()


class CaseCloseReasonViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CaseCloseReasonSerializer
    queryset = CaseCloseReason.objects.all()


class CitizenReportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CitizenReportAnonomizedSerializer
    queryset = CitizenReport.objects.all()
