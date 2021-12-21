import logging

from apps.cases.models import CaseClose
from apps.cases.serializers import CaseCloseSerializer
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
