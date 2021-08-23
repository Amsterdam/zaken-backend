from apps.users.permissions import CanPerformTask, rest_permission_classes_for_top
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import SAFE_METHODS
from rest_framework.viewsets import GenericViewSet

from .models import Visit
from .serializers import VisitSerializer


class VisitViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()

    def create(self, request):
        return super().create(request)

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanPerformTask)
        return super(VisitViewSet, self).get_permissions()
