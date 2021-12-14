import logging

from apps.cases.models import (
    Case,
    CaseClose,
    CaseProject,
    CaseReason,
    CaseState,
    CaseTheme,
    CitizenReport,
)
from apps.cases.serializers import (
    BWVMeldingenSerializer,
    BWVStatusSerializer,
    CaseCloseReasonSerializer,
    CaseCloseResultSerializer,
    CaseCloseSerializer,
    CaseCreateUpdateSerializer,
    CaseProjectSerializer,
    CaseReasonSerializer,
    CaseSerializer,
    CaseStateSerializer,
    CaseStateTypeSerializer,
    CaseThemeSerializer,
    CaseWorkflowSerializer,
    CitizenReportSerializer,
    LegacyCaseCreateSerializer,
    LegacyCaseUpdateSerializer,
    PushCaseStateSerializer,
    StartWorkflowSerializer,
    SubjectSerializer,
)
from apps.users.permissions import (
    CanCloseCase,
    CanCreateCase,
    rest_permission_classes_for_top,
)
from apps.workflow.serializers import (
    GenericCompletedTaskSerializer,
    WorkflowOptionSerializer,
)
from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class CaseStateViewSet(viewsets.ViewSet):
    """
    Pushes the case state
    """

    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseStateSerializer
    queryset = CaseState.objects.all()

    @action(
        detail=True,
        url_path="update-from-top",
        methods=["post"],
        serializer_class=PushCaseStateSerializer,
    )
    def update_from_top(self, request, pk):
        logger.info("Receiving pushed state update")
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            logger.error("Serializer error: {serializer.errors}")
            raise APIException(f"Serializer error: {serializer.errors}")

        try:
            case_state = CaseState.objects.get(id=pk)
            case_state.users.clear()
            user_emails = data.get("user_emails", [])
            logger.info(f"Updating CaseState {len(user_emails)} users")
            user_model = get_user_model()

            for user_email in user_emails:
                user_object, _ = user_model.objects.get_or_create(email=user_email)
                case_state.users.add(user_object)
                logger.info("Added user to CaseState")

            return Response(CaseStateSerializer(case_state).data)
        except Exception as e:
            logger.error(f"Could not process push data: {e}")
            raise logger(f"Could not push data: {e}")


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
