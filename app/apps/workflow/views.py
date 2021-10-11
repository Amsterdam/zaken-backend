from apps.users.permissions import rest_permission_classes_for_top
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from .models import CaseUserTask
from .serializers import CaseUserTaskListSerializer

role_parameter = OpenApiParameter(
    name="role",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Role",
)
completed_parameter = OpenApiParameter(
    name="completed",
    type=OpenApiTypes.STR,
    enum=["all", "completed", "not_completed"],
    location=OpenApiParameter.QUERY,
    required=False,
    description="Completed",
)


class CaseUserTaskViewSet(
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseUserTaskListSerializer
    queryset = CaseUserTask.objects.all()
    http_method_names = ["patch", "get"]

    @extend_schema(
        parameters=[
            role_parameter,
            completed_parameter,
        ],
        description="CaseUserTask filter query parameters",
        responses={200: CaseUserTaskListSerializer(many=True)},
    )
    def list(self, request):
        role = request.GET.get(role_parameter.name)
        completed = request.GET.get(completed_parameter.name, "not_completed")

        tasks = self.get_queryset()
        if role:
            tasks = tasks.filter(
                roles__contains=[
                    role,
                ]
            )

        if completed != "all":
            tasks = tasks.filter(
                completed=True if completed == "completed" else False,
            )

        serializer = CaseUserTaskListSerializer(
            tasks, many=True, context={"request": request}
        )

        return Response(serializer.data)
