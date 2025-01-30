from apps.main.pagination import LimitedOffsetPaginator
from apps.users.permissions import rest_permission_classes_for_top
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Visit
from .serializers import VisitSerializer
from .task_completion import complete_task_create_visit


class VisitViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = VisitSerializer
    queryset = Visit.objects.all()
    pagination_class = LimitedOffsetPaginator

    def create(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            complete_task_create_visit(serializer)
            return Response(
                data="Visit added",
                status=201,
            )
        else:
            return Response(
                data=serializer.errors,
                status=400,
            )
