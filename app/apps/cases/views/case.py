from apps.cases.models import Case, CaseStateType
from apps.cases.serializers import (
    AdvertisementSerializer,
    CaseSerializer,
    CitizenReportSerializer,
    SubjectSerializer,
)
from apps.events.mixins import CaseEventsMixin
from apps.main.filters import RelatedOrderingFilter
from apps.main.pagination import EmptyPagination
from apps.users.permissions import (
    CanCreateCase,
    CanCreateDigitalSurveillanceCase,
    rest_permission_classes_for_top,
)
from apps.workflow.models import CaseWorkflow, WorkflowOption
from apps.workflow.serializers import (
    CaseWorkflowSerializer,
    StartWorkflowSerializer,
    WorkflowOptionSerializer,
)
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response


class CharArrayFilter(filters.BaseCSVFilter, filters.CharFilter):
    pass


class CaseFilter(filters.FilterSet):
    from_start_date = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    open_cases = filters.BooleanFilter(method="get_open_cases")
    state_types = filters.ModelMultipleChoiceFilter(
        queryset=CaseStateType.objects.all(), method="get_state_types"
    )
    ton_ids = CharArrayFilter(field_name="ton_ids", lookup_expr="contains")
    street_name = filters.CharFilter(method="get_fuzy_street_name")
    number = filters.CharFilter(method="get_number")
    suffix = filters.CharFilter(method="get_suffix")
    postal_code = filters.CharFilter(method="get_postal_code")

    def get_fuzy_street_name(self, queryset, name, value):
        return queryset.filter(address__street_name__trigram_similar=value)

    def get_number(self, queryset, name, value):
        return queryset.filter(address__number=value)

    def get_suffix(self, queryset, name, value):
        return queryset.filter(
            Q(address__suffix__iexact=value) | Q(address_suffix_letter__iexact=value)
        )

    def get_open_cases(self, queryset, name, value):
        return queryset.filter(end_date__isnull=value)

    def get_postal_code(self, queryset, name, value):
        return queryset.filter(address__postal_code__iexact=value.replace(" ", ""))

    def get_state_types(self, queryset, name, value):
        if value:
            return queryset.filter(
                workflows__case_state_type__in=value,
            ).distinct()
        return queryset

    class Meta:
        model = Case
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
        ]


class StandardResultsSetPagination(EmptyPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


@extend_schema(
    parameters=[
        OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("from_start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("theme", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("reason", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("sensitive", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("open_cases", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("state_types", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("page_size", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("ton_ids", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
    ]
)
class CaseViewSet(
    CaseEventsMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    filter_backends = (
        filters.DjangoFilterBackend,
        RelatedOrderingFilter,
    )
    ordering_fields = "__all_related__"
    filterset_class = CaseFilter
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action == "create" and self.request.method not in SAFE_METHODS:
            if self.request.data.get("reason_id") in settings.DIGITAL_SURVEILLANCE_IDS:
                self.permission_classes.append(CanCreateDigitalSurveillanceCase)
            else:
                self.permission_classes.append(CanCreateCase)
        return super(CaseViewSet, self).get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request, "user") and not self.request.user.has_perm(
            "users.access_sensitive_dossiers"
        ):
            queryset = queryset.exclude(sensitive=True)
        return queryset

    @extend_schema(
        description="Get tasks for this Case",
        responses={status.HTTP_200_OK: CaseWorkflowSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="tasks")
    def get_tasks(self, request, pk):
        case = self.get_object()
        request.user
        queryset = CaseWorkflow.objects.filter(
            case=case, tasks__isnull=False, tasks__completed=False
        ).distinct()
        paginator = LimitOffsetPagination()
        context = paginator.paginate_queryset(queryset, request)
        serializer = CaseWorkflowSerializer(
            context, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the Subjects associated with the given theme",
        responses={status.HTTP_200_OK: SubjectSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="subjects",
        methods=["get"],
    )
    def subjects(self, request, pk):
        paginator = LimitOffsetPagination()
        case = self.get_object()
        query_set = case.subjects.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = SubjectSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Get WorkflowOption for this Case",
        responses={status.HTTP_200_OK: WorkflowOptionSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="processes",
        methods=["get"],
        serializer_class=WorkflowOptionSerializer,
    )
    def get_workflow_options(self, request, pk):
        """
        Get WorkflowOption instances for this case. Currently this case detail linking
        does not do anything. This is future proofing this rest call so that we can
        show and not show processes based on the current state of the case
        (for example not show the summon/aanschrijving process when we are in visit state)
        """
        case = get_object_or_404(Case, pk=pk)
        serializer = WorkflowOptionSerializer(
            WorkflowOption.objects.filter(theme=case.theme), many=True
        )
        return Response(serializer.data)

    @extend_schema(
        description="Start based on a WorkflowOption",
    )
    @action(
        detail=True,
        url_path="processes/start",
        methods=["post"],
        serializer_class=StartWorkflowSerializer,
    )
    def start_process(self, request, pk):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            case = self.get_object()
            instance = data["workflow_option_id"]

            workflow_type = CaseWorkflow.WORKFLOW_TYPE_SUB
            if instance.to_directing_proccess:
                workflow_type = CaseWorkflow.WORKFLOW_TYPE_DIRECTOR

            CaseWorkflow.objects.create(
                case=case,
                workflow_type=workflow_type,
                workflow_message_name=instance.message_name,
            )

            return Response(
                data=f"Workflow has started {str(instance)}",
                status=status.HTTP_200_OK,
            )

        return Response(
            data="Workflow has not started. serializer not valid",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @extend_schema(
        description="Create citizen report instance associated with this case",
        responses={status.HTTP_200_OK: CitizenReportSerializer()},
    )
    @action(
        detail=True,
        url_path="citizen-reports",
        methods=["post"],
        serializer_class=CitizenReportSerializer,
    )
    def citizen_reports(self, request, pk):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.create(serializer.validated_data)
            return Response(
                data="CitizenReport added",
                status=status.HTTP_200_OK,
            )
        return Response(
            data="CitizenReport error. serializer not valid",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @extend_schema(
        description="Gets the Advertisements associated with this case",
        responses={status.HTTP_200_OK: AdvertisementSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="advertisements",
        methods=["get"],
    )
    def advertisements(self, request, pk):
        paginator = LimitOffsetPagination()
        case = self.get_object()
        query_set = case.advertisements.all()
        context = paginator.paginate_queryset(query_set, request)
        serializer = AdvertisementSerializer(context, many=True)
        return paginator.get_paginated_response(serializer.data)
