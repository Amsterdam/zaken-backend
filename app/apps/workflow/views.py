from apps.addresses.models import District, HousingCorporation
from apps.cases.models import (
    Case,
    CaseProject,
    CaseReason,
    CaseStateType,
    CaseTheme,
    Subject,
    Tag,
)
from apps.main.filters import RelatedOrderingFilter
from apps.main.pagination import EmptyPagination
from apps.summons.serializers import SummonTypeSerializer
from apps.users.auth_apps import TopKeyAuth
from apps.users.permissions import CanAccessSensitiveCases, IsInAuthorizedRealm
from apps.workflow.serializers import (
    CaseUserTaskSerializer,
    CaseUserTaskTaskNameSerializer,
    GenericCompletedTaskCreateSerializer,
    GenericCompletedTaskSerializer,
)
from apps.workflow.utils import map_variables_on_task_spec_form
from django.db.models import Q
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
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
    completed = filters.BooleanFilter()
    district = filters.ModelMultipleChoiceFilter(
        queryset=District.objects.all(), method="get_district"
    )
    district_name = filters.ModelMultipleChoiceFilter(
        queryset=District.objects.all(),
        method="get_district",
        to_field_name="name",
    )
    from_start_date = filters.DateFilter(
        field_name="case__start_date", lookup_expr="gte"
    )
    housing_corporation = filters.ModelMultipleChoiceFilter(
        queryset=HousingCorporation.objects.all(),
        method="get_housing_corporation",
    )
    housing_corporation_isnull = filters.BooleanFilter(
        method="filter_housing_corporation_isnull"
    )
    is_enforcement_request = filters.BooleanFilter(
        method="get_enforcement_request_cases"
    )
    name = filters.ModelMultipleChoiceFilter(
        queryset=CaseUserTask.objects.filter(completed=False),
        to_field_name="name",
    )
    number = filters.CharFilter(method="get_number")
    open_cases = filters.BooleanFilter(method="get_open_cases")
    postal_code = filters.CharFilter(method="get_postal_code")
    project = filters.ModelMultipleChoiceFilter(
        queryset=CaseProject.objects.all(), method="get_project"
    )
    project_name = filters.ModelMultipleChoiceFilter(
        queryset=CaseProject.objects.all(),
        method="get_project",
        to_field_name="name",
    )
    reason = filters.ModelMultipleChoiceFilter(
        queryset=CaseReason.objects.all(), method="get_reason"
    )
    reason_name = filters.ModelMultipleChoiceFilter(
        queryset=CaseReason.objects.all(),
        method="get_reason",
        to_field_name="name",
    )
    role = filters.CharFilter(method="get_role")
    sensitive = filters.BooleanFilter(field_name="case__sensitive")
    start_date = filters.DateFilter(field_name="case__start_date")
    state_types = filters.ModelMultipleChoiceFilter(
        queryset=CaseStateType.objects.all(), method="get_state_types"
    )
    street_name = filters.CharFilter(method="get_fuzy_street_name")
    suffix = filters.CharFilter(method="get_suffix")
    subject = filters.ModelMultipleChoiceFilter(
        queryset=Subject.objects.all(),
        method="get_subject",
    )
    subject_name = filters.ModelMultipleChoiceFilter(
        queryset=Subject.objects.all(),
        method="get_subject",
        to_field_name="name",
    )
    tag = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        method="get_tag",
    )
    theme = filters.ModelMultipleChoiceFilter(
        queryset=CaseTheme.objects.all(),
        method="get_theme",
    )
    theme_name = filters.ModelMultipleChoiceFilter(
        queryset=CaseTheme.objects.all(),
        method="get_theme",
        to_field_name="name",
    )
    ton_ids = CharArrayFilter(method="get_ton_ids")

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
            | Q(case__address__suffix_letter__iexact=value)
        )

    def get_open_cases(self, queryset, name, value):
        return queryset.filter(case__end_date__isnull=value)

    def get_postal_code(self, queryset, name, value):
        return queryset.filter(
            case__address__postal_code__iexact=value.replace(" ", "")
        )

    def get_enforcement_request_cases(self, queryset, name, value):
        return queryset.filter(case__is_enforcement_request=value)

    def get_state_types(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__workflows__completed=False,
                case__workflows__case_state_type__isnull=False,
                case__workflows__case_state_type__in=value,
            ).distinct()
        return queryset

    def get_subject(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__subjects__in=value,
            ).distinct()
        return queryset

    def get_tag(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__tags__in=value,
            ).distinct()
        return queryset

    def get_theme(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__theme__in=value,
            )
        return queryset

    def get_reason(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__reason__in=value,
            )
        return queryset

    def get_project(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__project__in=value,
            )
        return queryset

    def get_district(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__address__district__in=value,
            )
        return queryset

    def get_housing_corporation(self, queryset, name, value):
        if value:
            return queryset.filter(case__address__housing_corporation__in=value)
        return queryset

    def filter_housing_corporation_isnull(self, queryset, name, value):
        return queryset.filter(case__address__housing_corporation__isnull=value)

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
            "name",
        ]


class StandardResultsSetPagination(EmptyPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


@extend_schema(
    parameters=[
        OpenApiParameter("completed", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("district", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("district_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("due_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("from_start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter(
            "housing_corporation", OpenApiTypes.NUMBER, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "housing_corporation_isnull", OpenApiTypes.BOOL, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "is_enforcement_request", OpenApiTypes.BOOL, OpenApiParameter.QUERY
        ),
        OpenApiParameter("name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("page_size", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("project", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("project_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("open_cases", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("owner", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("reason", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("reason_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("role", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("sensitive", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("state_types", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("subject", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("subject_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("tag", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("theme", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("theme_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("ton_ids", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
    ]
)
class CaseUserTaskViewSet(
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [(IsInAuthorizedRealm & CanAccessSensitiveCases) | TopKeyAuth]
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
        if (
            self.action in ("list",)
            and hasattr(self.request, "user")
            and not self.request.user.has_perm("users.access_sensitive_dossiers")
        ):
            queryset = queryset.exclude(case__sensitive=True)
        return queryset

    @extend_schema(
        description="Gets all task names",
        responses={status.HTTP_200_OK: CaseUserTaskTaskNameSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="task-names",
    )
    def task_names(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.distinct("name").order_by("name")
        serializer = CaseUserTaskTaskNameSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Gets all reason names",
        responses={
            status.HTTP_200_OK: serializers.ListSerializer(
                child=serializers.CharField()
            )
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="reason-names",
    )
    def reason_names(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = (
            queryset.distinct("case__reason__name")
            .order_by("case__reason__name")
            .values_list("case__reason__name", flat=True)
        )
        serializer = serializers.ListSerializer(queryset, child=serializers.CharField())
        return Response(serializer.data)

    @extend_schema(
        description="Gets all district names",
        responses={
            status.HTTP_200_OK: serializers.ListSerializer(
                child=serializers.CharField()
            )
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="district-names",
    )
    def district_names(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = (
            queryset.distinct("case__address__district__name")
            .order_by("case__address__district__name")
            .values_list("case__address__district__name", flat=True)
        )
        serializer = serializers.ListSerializer(queryset, child=serializers.CharField())
        return Response(serializer.data)

    @extend_schema(
        description="Gets the SummonTypes associated with the given  task id",
        responses={status.HTTP_200_OK: SummonTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="summon-types",
        methods=["get"],
    )
    def summon_types(self, request, pk):
        paginator = LimitOffsetPagination()
        caseUserTask = self.get_object()
        theme = caseUserTask.case.theme
        exclude_options = caseUserTask.workflow.get_workflow_exclude_options()
        exclude_names = caseUserTask.workflow.get_workflow_exclude_names()
        # Theres's always an exclude_options or a exclude_names. Version is always above/equal or below "7.3.0".
        query_set = theme.summon_types.exclude(
            workflow_option__in=exclude_options
        ).exclude(name__in=exclude_names)

        context = paginator.paginate_queryset(query_set, request)
        serializer = SummonTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)


class GenericCompletedTaskFilter(filters.FilterSet):
    task_name = filters.CharFilter(field_name="task_name")
    description = filters.CharFilter(field_name="description")
    from_date_added = filters.DateFilter(field_name="date_added", lookup_expr="gte")
    to_date_added = filters.DateFilter(field_name="date_added", lookup_expr="lt")
    open_cases = filters.BooleanFilter(method="get_open_cases")
    case = filters.ModelMultipleChoiceFilter(
        queryset=Case.objects.all(), method="get_case"
    )
    case__project = filters.ModelMultipleChoiceFilter(
        queryset=CaseProject.objects.all(), method="get_project"
    )
    case__reason = filters.ModelMultipleChoiceFilter(
        queryset=CaseReason.objects.all(), method="get_reason"
    )

    def get_open_cases(self, queryset, name, value):
        return queryset.filter(case__end_date__isnull=value)

    def get_case(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__in=value,
            )
        return queryset

    def get_project(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__project__in=value,
            )
        return queryset

    def get_reason(self, queryset, name, value):
        if value:
            return queryset.filter(
                case__reason__in=value,
            )
        return queryset

    class Meta:
        model = GenericCompletedTask
        fields = [
            "case",
            "task_name",
            "description",
        ]


class StandardResultsSetPagination(EmptyPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


@extend_schema(
    parameters=[
        OpenApiParameter("task_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("description", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("from_date_added", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("to_date_added", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("case", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("case__theme", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("case__reason", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
    ]
)
class GenericCompletedTaskViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = GenericCompletedTaskSerializer
    queryset = GenericCompletedTask.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = GenericCompletedTaskFilter
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        description="Complete GenericCompletedTask",
        responses={200: None},
    )
    @action(
        detail=False,
        url_path="complete",
        methods=["post"],
        serializer_class=GenericCompletedTaskCreateSerializer,
    )
    def complete_task(self, request):
        context = {"request": self.request}

        serializer = GenericCompletedTaskCreateSerializer(
            data=request.data, context=context
        )

        if serializer.is_valid():
            data = serializer.validated_data

            variables = data.get("variables", {})
            task = CaseUserTask.objects.get(
                id=data["case_user_task_id"], completed=False
            )

            if task.case.sensitive and not request.user.has_perm(
                "users.access_sensitive_dossiers"
            ):
                return Response(status=status.HTTP_403_FORBIDDEN)

            from .user_tasks import get_task_by_name

            user_task_type = get_task_by_name(task.task_name)
            user_task = user_task_type(task)
            if user_task and user_task.mapped_form_data(variables):
                variables["mapped_form_data"] = user_task.mapped_form_data(variables)
            else:
                variables["mapped_form_data"] = map_variables_on_task_spec_form(
                    variables, task.form
                )
            data.update(
                {
                    "description": task.name,
                    "task_name": task.task_name,
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
