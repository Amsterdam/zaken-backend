import logging

from apps.cases.models import (
    CaseClose,
    CaseCloseReason,
    CaseCloseResult,
    CaseState,
    CitizenReport,
)
from apps.cases.serializers import (
    CaseCloseReasonSerializer,
    CaseCloseResultSerializer,
    CaseCloseSerializer,
    CaseStateSerializer,
    CitizenReportAnonomizedSerializer,
)
from apps.users.permissions import CanCloseCase, rest_permission_classes_for_top
from django.db import transaction
from rest_framework import mixins, viewsets
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

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

    def create(self, request):
        with transaction.atomic():
            serializer = self.serializer_class(
                data=request.data,
                context={"request": request},
            )
            if serializer.is_valid():
                case_close = serializer.create(serializer.validated_data)
                CaseState.objects.get_or_create(
                    case=case_close.case,
                    status=CaseState.CaseStateChoice.AFGESLOTEN,
                )
                case_close.case.close_case()
                return Response(serializer.data)


class CaseCloseResultViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CaseCloseResultSerializer
    queryset = CaseCloseResult.objects.all()


class CaseCloseReasonViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CaseCloseReasonSerializer
    queryset = CaseCloseReason.objects.all()


class CitizenReportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CitizenReportAnonomizedSerializer
    queryset = CitizenReport.objects.all()


class CaseStateViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CaseStateSerializer
    queryset = CaseState.objects.all()
