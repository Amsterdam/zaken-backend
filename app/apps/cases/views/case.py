from apps.addresses.utils import search
from apps.cases.models import Case, CaseState, CitizenReport
from apps.cases.serializers import (
    CaseCreateUpdateSerializer,
    CaseSerializer,
    CaseWorkflowSerializer,
    CitizenReportSerializer,
    StartWorkflowSerializer,
    SubjectSerializer,
)
from apps.cases.swagger_parameters import postal_code as postal_code_parameter
from apps.cases.swagger_parameters import street_name as street_name_parameter
from apps.cases.swagger_parameters import street_number as street_number_parameter
from apps.cases.swagger_parameters import suffix as suffix_parameter
from apps.cases.swagger_parameters import theme as theme_parameter
from apps.cases.swagger_parameters import ton_ids as ton_ids_parameter
from apps.events.mixins import CaseEventsMixin
from apps.users.permissions import CanCreateCase, rest_permission_classes_for_top
from apps.workflow.models import CaseWorkflow, WorkflowOption
from apps.workflow.serializers import WorkflowOptionSerializer
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters as rest_filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response


class CaseOrderingFilter(filters.FilterSet):
    from_start_date = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    open_cases = filters.BooleanFilter(method="get_open_cases")
    open_status = filters.ModelMultipleChoiceFilter(
        queryset=CaseState.objects.all(), method="get_open_cases_with_statuses"
    )

    def get_open_cases(self, queryset, name, value):
        return queryset.filter(end_date__isnull=value)

    def get_open_cases_with_statuses(self, queryset, name, value):
        if value:
            return queryset.filter(
                case_states__end_date__isnull=True,
                case_states__status__id__in=list(
                    map(lambda casestate: casestate.id, value)
                ),
            )
        return queryset

    class Meta:
        model = Case
        fields = ["start_date", "from_start_date", "theme", "reason", "sensitive"]


class StandardResultsSetPagination(PageNumberPagination):
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
        OpenApiParameter("open_status", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("page_size", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY),
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
    filter_backends = (filters.DjangoFilterBackend, rest_filters.OrderingFilter)
    ordering_fields = "__all__"
    filterset_class = CaseOrderingFilter
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action == "create" and self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanCreateCase)
        return super(CaseViewSet, self).get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = self.perform_create(serializer)

        citizen_report_data = {"case": case.id}
        citizen_report_data.update(request.data)
        citizen_report_serializer = CitizenReportSerializer(
            data=citizen_report_data,
            context={"request": request},
        )
        if citizen_report_serializer.is_valid():
            citizen_report_serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        return serializer.save()

    def get_serializer_class(self, *args, **kwargs):
        if self.action in ["create", "update"]:
            return CaseCreateUpdateSerializer

        return self.serializer_class

    # @extend_schema(
    #     parameters=[
    #         date_parameter,
    #         start_date_parameter,
    #         open_cases_parameter,
    #         theme_parameter,
    #         reason_parameter,
    #         open_status_parameter,
    #         no_pagination_parameter,
    #     ],
    #     description="Case filter query parameters",
    #     responses={200: CaseSerializer(many=True)},
    # )
    # def list(self, request):
    #     date = request.GET.get(date_parameter.name, None)
    #     start_date = request.GET.get(start_date_parameter.name, None)
    #     open_cases = request.GET.get(open_cases_parameter.name, None)
    #     theme = request.GET.get(theme_parameter.name, None)
    #     reason = request.GET.get(reason_parameter.name, None)
    #     open_status = request.GET.get(open_status_parameter.name, None)
    #     no_pagination = request.GET.get(no_pagination_parameter.name, None)

    #     queryset = self.get_queryset()

    #     if date:
    #         queryset = queryset.filter(start_date=date)
    #     if start_date:
    #         queryset = queryset.filter(start_date__gte=start_date)
    #     if open_cases:
    #         open_cases = open_cases == "true"
    #         queryset = queryset.filter(end_date__isnull=open_cases)
    #     if theme:
    #         queryset = queryset.filter(theme=theme)
    #     if reason:
    #         queryset = queryset.filter(reason=reason)
    #     if open_status:
    #         queryset = queryset.filter(
    #             case_states__end_date__isnull=True,
    #             case_states__status__id__in=open_status.split(","),
    #         ).distinct()

    #     if no_pagination == "true":
    #         serializer = CaseSerializer(queryset, many=True)
    #         return Response(serializer.data)

    #     paginator = LimitOffsetPagination()
    #     context = paginator.paginate_queryset(queryset, request)
    #     serializer = CaseSerializer(context, many=True)

    #     return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        parameters=[
            postal_code_parameter,
            street_number_parameter,
            street_name_parameter,
            suffix_parameter,
            theme_parameter,
            ton_ids_parameter,
        ],
        description="Search query parameters",
        responses={200: CaseSerializer(many=True)},
        operation=None,
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        postal_code = request.GET.get(postal_code_parameter.name, None)
        street_name = request.GET.get(street_name_parameter.name, None)
        number = request.GET.get(street_number_parameter.name, None)
        suffix = request.GET.get(suffix_parameter.name, None)
        theme = request.GET.get(theme_parameter.name, None)
        ton_ids = request.GET.get(ton_ids_parameter.name, None)

        if postal_code is None and street_name is None and ton_ids is None:
            return HttpResponseBadRequest(
                "A postal_code or street_name or ton_ids queryparameter should be provided"
            )
        if postal_code is not None and number is None:
            return HttpResponseBadRequest("number queryparameter is required")
        if street_name is not None and number is None:
            return HttpResponseBadRequest("number queryparameter is required")

        address_queryset = search(
            street_name=street_name,
            postal_code=postal_code,
            number=number,
            suffix=suffix,
        )

        cases = Case.objects.none()
        for address in address_queryset:
            cases = cases | address.cases.all()

        cases = cases.filter(end_date=None)

        if theme:
            cases = cases.filter(theme=theme)

        if ton_ids:
            cases = cases.filter(ton_ids__overlap=ton_ids.split(","))

        paginator = LimitOffsetPagination()
        context = paginator.paginate_queryset(cases, request)
        serializer = CaseSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

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
            data = serializer.validated_data

            citizen_report = CitizenReport(**data)
            citizen_report.save()
            return Response(
                data="CitizenReport added",
                status=status.HTTP_200_OK,
            )
        return Response(
            data="CitizenReport error. serializer not valid",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
