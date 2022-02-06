from apps.cases.models import CaseStateType
from apps.main.filters import RelatedOrderingFilter
from apps.main.pagination import EmptyPagination
from apps.users.permissions import rest_permission_classes_for_top
from apps.workflow.serializers import (
    CaseUserTaskSerializer,
    GenericCompletedTaskSerializer,
)
from apps.workflow.utils import map_variables_on_task_spec_form
from django.db.models import Q
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CaseUserTask, GenericCompletedTask

role_parameter = OpenApiParameter(
    name="role",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Role",
)
theme_parameter = OpenApiParameter(
    name="theme",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Theme",
)
completed_parameter = OpenApiParameter(
    name="completed",
    type=OpenApiTypes.STR,
    enum=["all", "completed", "not_completed"],
    location=OpenApiParameter.QUERY,
    required=False,
    description="Completed",
)


class CharArrayFilter(filters.BaseCSVFilter, filters.CharFilter):
    pass


class CaseUserTaskFilter(filters.FilterSet):
    from_start_date = filters.DateFilter(
        field_name="case__start_date", lookup_expr="gte"
    )
    start_date = filters.DateFilter(field_name="case__start_date")
    reason = filters.CharFilter(field_name="case__reason")
    sensitive = filters.BooleanFilter(field_name="case__sensitive")
    open_cases = filters.BooleanFilter(method="get_open_cases")
    state_types = filters.ModelMultipleChoiceFilter(
        queryset=CaseStateType.objects.all(), method="get_state_types"
    )
    ton_ids = CharArrayFilter(method="get_ton_ids")
    street_name = filters.CharFilter(method="get_fuzy_street_name")
    number = filters.CharFilter(method="get_number")
    suffix = filters.CharFilter(method="get_suffix")
    postal_code = filters.CharFilter(method="get_postal_code")
    completed = filters.BooleanFilter()
    role = filters.CharFilter(method="get_role")
    theme = filters.CharFilter(field_name="case__theme__name")

    def get_role(self, queryset, name, value):
        return queryset.filter(roles__contains=[value])

    def get_ton_ids(self, queryset, name, value):
        return queryset.filter(case__ton_ids__contains=value)

    def get_fuzy_street_name(self, queryset, name, value):
        return queryset.filter(case__address__street_name__trigram_similar=value)

    def get_number(self, queryset, name, value):
        return queryset.filter(case__address__number=value)

    def get_suffix(self, queryset, name, value):
        return queryset.filter(
            Q(case__address__suffix__iexact=value)
            | Q(case__address_suffix_letter__iexact=value)
        )

    def get_open_cases(self, queryset, name, value):
        return queryset.filter(case__end_date__isnull=value)

    def get_postal_code(self, queryset, name, value):
        return queryset.filter(
            case__address__postal_code__iexact=value.replace(" ", "")
        )

    def get_state_types(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__workflows__case_state_type__in=value,
            ).distinct()
        return queryset

    class Meta:
        model = CaseUserTask
        fields = [
            "start_date",
            "from_start_date",
            "theme",
            "reason",
            "sensitive",
            "ton_ids",
            "street_name",
            "number",
            "suffix",
            "postal_code",
            "completed",
            "role",
            "owner",
        ]


class StandardResultsSetPagination(EmptyPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


@extend_schema(
    parameters=[
        OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("from_start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("theme", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("reason", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("sensitive", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("open_cases", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("state_types", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("page_size", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("ton_ids", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("completed", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("role", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("due_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("owner", OpenApiTypes.STR, OpenApiParameter.QUERY),
    ]
)
class CaseUserTaskViewSet(
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseUserTaskSerializer
    queryset = CaseUserTask.objects.all()
    http_method_names = ["patch", "get"]

    filter_backends = (
        filters.DjangoFilterBackend,
        RelatedOrderingFilter,
    )
    ordering_fields = "__all_related__"
    filterset_class = CaseUserTaskFilter
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request, "user") and not self.request.user.has_perm(
            "users.access_sensitive_dossiers"
        ):
            queryset = queryset.exclude(case__sensitive=True)
        return queryset


class GenericCompletedTaskViewSet(viewsets.ViewSet):
    serializer_class = GenericCompletedTaskSerializer
    queryset = GenericCompletedTask.objects.all()

    @extend_schema(
        description="Complete GenericCompletedTask",
        responses={200: None},
    )
    @action(
        detail=False,
        url_path="complete",
        methods=["post"],
        serializer_class=GenericCompletedTaskSerializer,
    )
    def complete_task(self, request):
        context = {"request": self.request}

        serializer = GenericCompletedTaskSerializer(data=request.data, context=context)

        if serializer.is_valid():
            data = serializer.validated_data

            variables = data.get("variables", {})
            task = CaseUserTask.objects.get(
                id=data["case_user_task_id"], completed=False
            )
            variables["mapped_form_data"] = map_variables_on_task_spec_form(
                variables, task.form
            )
            data.update(
                {
                    "description": task.name,
                    "variables": variables,
                }
            )

            try:
                GenericCompletedTask.objects.create(**data)
                return Response(
                    f"CaseUserTask {data['case_user_task_id']} has been completed"
                )
            except Exception as e:
                raise e

        return Response(status=status.HTTP_400_BAD_REQUEST)
