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


class CaseUserTaskViewSet(
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseUserTaskListSerializer
    queryset = CaseUserTask.objects.filter(completed=False)
    http_method_names = ["patch", "get"]

    @extend_schema(
        parameters=[
            role_parameter,
        ],
        description="CaseUserTask filter query parameters",
        responses={200: CaseUserTaskListSerializer(many=True)},
    )
    def list(self, request):
        role = request.GET.get(role_parameter.name)

        tasks = self.get_queryset()
        if role:
            tasks = tasks.filter(
                roles__contains=[
                    role,
                ]
            )

        serializer = CaseUserTaskListSerializer(
            tasks, many=True, context={"request": request}
        )

        return Response(serializer.data)
