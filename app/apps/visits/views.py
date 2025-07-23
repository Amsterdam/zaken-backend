from apps.main.pagination import LimitedOffsetPaginator
from apps.users.permissions import rest_permission_classes_for_top
from apps.workflow.models import CaseWorkflow
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet

from .models import Visit
from .serializers import VisitSerializer


class VisitViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()
    pagination_class = LimitedOffsetPaginator

    def perform_create(self, serializer):
        case = serializer.validated_data.get("case")

        # Check if this is an additional visit
        is_additional = False
        if case:
            workflow = CaseWorkflow.objects.filter(case=case).first()
            if (
                workflow
                and workflow.case_state_type
                and "aanvullend" in workflow.case_state_type.name.lower()
            ):
                is_additional = True

        serializer.save(is_additional=is_additional)
