import io
import logging
import operator
import re
from functools import reduce

from apps.addresses.models import District, HousingCorporation
from apps.cases.models import (
    Case,
    CaseDocument,
    CaseProject,
    CaseReason,
    CaseStateType,
    CaseTheme,
    Subject,
    Tag,
)
from apps.cases.serializers import (
    AdvertisementSerializer,
    CaseBagIdsSerializer,
    CaseCreateSerializer,
    CaseDataSerializer,
    CaseDetailSerializer,
    CaseDocumentSerializer,
    CaseDocumentUploadSerializer,
    CaseSerializer,
    CaseSimplifiedSerializer,
    CitizenReportSerializer,
    DocumentTypeSerializer,
    SubjectSerializer,
)
from apps.events.mixins import CaseEventsMixin
from apps.main.filters import RelatedOrderingFilter
from apps.main.pagination import EmptyPagination
from apps.openzaak.helpers import (
    create_document,
    delete_document,
    get_document,
    get_document_inhoud,
    get_document_types,
    get_documents_meta,
    get_open_zaak_case,
    get_zaaktype,
)
from apps.schedules.models import DaySegment, Priority, Schedule, WeekSegment
from apps.users.auth_apps import TopKeyAuth
from apps.users.models import ScopedTokenAuth
from apps.users.permissions import (
    CanAccessSensitiveCases,
    IsInAuthorizedRealm,
    ScopedViewPermission,
)
from apps.workflow.models import CaseUserTask, CaseWorkflow, WorkflowOption
from apps.workflow.serializers import (
    CaseWorkflowSerializer,
    StartWorkflowSerializer,
    WorkflowOptionSerializer,
)
from django.db.models import OuterRef, Q, Subquery
from django.forms.fields import CharField, MultipleChoiceField
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action, parser_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from utils.mimetypes import get_mimetype

logger = logging.getLogger(__name__)


class MultipleValueField(MultipleChoiceField):
    def __init__(self, *args, field_class, **kwargs):
        self.inner_field = field_class()
        super().__init__(*args, **kwargs)

    def valid_value(self, value):
        return self.inner_field.validate(value)

    def clean(self, values):
        return values and [self.inner_field.clean(value) for value in values]


class MultipleValueFilter(filters.Filter):
    field_class = MultipleValueField

    def __init__(self, *args, field_class, **kwargs):
        kwargs.setdefault("lookup_expr", "in")
        super().__init__(*args, field_class=field_class, **kwargs)


class CharArrayFilter(filters.BaseCSVFilter, filters.CharFilter):
    pass


class CaseFilter(filters.FilterSet):
    district = filters.ModelMultipleChoiceFilter(
        queryset=District.objects.all(), method="get_district"
    )
    district_name = filters.ModelMultipleChoiceFilter(
        queryset=District.objects.all(),
        method="get_district",
        to_field_name="name",
    )
    from_start_date = filters.DateFilter(field_name="start_date", lookup_expr="gte")
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
    number = filters.CharFilter(method="get_number")
    open_cases = filters.BooleanFilter(method="get_open_cases")
    postal_code = filters.CharFilter(method="get_postal_code")
    postal_code_range = MultipleValueFilter(
        field_class=CharField, method="get_postal_code_range"
    )
    priority = filters.ModelMultipleChoiceFilter(
        queryset=Priority.objects.all(),
        method="get_schedule_priority",
    )
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
    schedule_day_segment = filters.ModelMultipleChoiceFilter(
        queryset=DaySegment.objects.all(),
        method="get_schedule_day_segment",
    )
    schedule_from_date_added = filters.DateTimeFilter(
        method="get_schedule_from_date_added",
    )
    schedule_housing_corporation_combiteam = filters.BooleanFilter(
        method="get_schedule_housing_corporation_combiteam"
    )
    schedule_visit_from = filters.DateTimeFilter(
        method="get_schedule_visit_from",
    )
    schedule_week_segment = filters.ModelMultipleChoiceFilter(
        queryset=WeekSegment.objects.all(),
        method="get_schedule_week_segment",
    )
    state_types = filters.ModelMultipleChoiceFilter(
        queryset=CaseStateType.objects.all(), method="get_state_types"
    )
    state_types__name = filters.ModelMultipleChoiceFilter(
        queryset=CaseStateType.objects.all(),
        method="get_state_types",
        to_field_name="name",
    )
    street_name = filters.CharFilter(method="get_street_name")
    subject = filters.ModelMultipleChoiceFilter(
        queryset=Subject.objects.all(),
        method="get_subject",
    )
    subject_name = filters.ModelMultipleChoiceFilter(
        queryset=Subject.objects.all(),
        method="get_subject",
        to_field_name="name",
    )
    suffix = filters.CharFilter(method="get_suffix")
    tag = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(), method="get_tag"
    )
    task = filters.ModelMultipleChoiceFilter(
        queryset=CaseUserTask.objects.all(),
        method="get_task",
        to_field_name="task_name",
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
    ton_ids = CharArrayFilter(field_name="ton_ids", lookup_expr="contains")

    def get_annotated_qs_by_schedule_type(self, queryset, type, value):
        last_schedule = Schedule.objects.filter(case=OuterRef("pk")).order_by(
            "-date_modified"
        )
        return queryset.annotate(
            last_schedule_field=Subquery(last_schedule.values(type)[:1])
        )

    def get_schedule_day_segment(self, queryset, name, value):
        if value:
            queryset = self.get_annotated_qs_by_schedule_type(
                queryset, "day_segment", value
            )
            return queryset.filter(last_schedule_field__in=value)
        return queryset

    def get_schedule_week_segment(self, queryset, name, value):
        if value:
            queryset = self.get_annotated_qs_by_schedule_type(
                queryset, "week_segment", value
            )
            return queryset.filter(last_schedule_field__in=value)
        return queryset

    def get_schedule_visit_from(self, queryset, name, value):
        if value:
            queryset = self.get_annotated_qs_by_schedule_type(
                queryset, "visit_from_datetime", value
            )
            return queryset.filter(
                Q(last_schedule_field__lte=value) | Q(last_schedule_field__isnull=True)
            )
        return queryset

    def get_schedule_from_date_added(self, queryset, name, value):
        if value:
            queryset = self.get_annotated_qs_by_schedule_type(
                queryset, "date_added", value
            )
            return queryset.filter(last_schedule_field__gte=value)
        return queryset

    def get_schedule_priority(self, queryset, name, value):
        if value:
            queryset = self.get_annotated_qs_by_schedule_type(
                queryset, "priority", value
            )
            return queryset.filter(last_schedule_field__in=value)
        return queryset

    def get_schedule_housing_corporation_combiteam(self, queryset, name, value):
        queryset = self.get_annotated_qs_by_schedule_type(
            queryset, "housing_corporation_combiteam", value
        )
        return queryset.filter(last_schedule_field=value)

    def get_street_name(self, queryset, name, value):
        """
        Searches by street name or by a combination of postal code and house number in the format '1234AB 59'.
        """
        # Pattern to match a postal code followed by a house number
        pattern = r"^[0-9]{4}[a-zA-Z]{2} \d+$"

        value = value.strip()
        if re.match(pattern, value):
            postal_code, house_number = value.split(" ", 1)
            house_number = int(house_number)

            return queryset.filter(
                address__postal_code__iexact=postal_code, address__number=house_number
            )

        # Search for street name
        return queryset.filter(address__street_name__icontains=value)

    def get_number(self, queryset, name, value):
        return queryset.filter(address__number=value)

    def get_suffix(self, queryset, name, value):
        return queryset.filter(
            Q(address__suffix__iexact=value) | Q(address__suffix_letter__iexact=value)
        )

    def get_housing_corporation(self, queryset, name, value):
        if value:
            return queryset.filter(address__housing_corporation__in=value)
        return queryset

    def filter_housing_corporation_isnull(self, queryset, name, value):
        return queryset.filter(address__housing_corporation__isnull=value)

    def get_open_cases(self, queryset, name, value):
        return queryset.filter(end_date__isnull=value)

    def get_enforcement_request_cases(self, queryset, name, value):
        return queryset.filter(is_enforcement_request=value)

    def get_postal_code(self, queryset, name, value):
        return queryset.filter(address__postal_code__iexact=value.replace(" ", ""))

    def get_postal_code_range(self, queryset, name, value):
        postal_code_numbers = [v.split("-") for v in value if len(v.split("-")) == 2]
        postal_code_numbers = [
            str(p)
            for v in postal_code_numbers
            if int(v[0]) <= int(v[1])
            for p in range(int(v[0]), int(v[1]) + 1)
        ]
        postal_code_numbers = list(set(postal_code_numbers))
        postal_code_numbers = (
            Q(address__postal_code__icontains=str(p)) for p in postal_code_numbers
        )
        return queryset.filter(reduce(operator.or_, postal_code_numbers))

    def get_state_types(self, queryset, name, value):
        if value:
            return queryset.filter(
                workflows__completed=False,
                workflows__case_state_type__isnull=False,
                workflows__case_state_type__in=value,
            ).distinct()
        return queryset

    def get_task(self, queryset, name, value):
        # Filter here instead of the queryset to prevent exceptions when there are no open tasks with a speciifc state
        value = [task for task in value if not task.completed]
        if value:
            return queryset.filter(
                workflows__completed=False,
                workflows__tasks__in=value,
            )
        return queryset

    def get_project(self, queryset, name, value):
        if value:
            return queryset.filter(
                project__in=value,
            )
        return queryset

    def get_subject(self, queryset, name, value):
        if value:
            return queryset.filter(
                subjects__in=value,
            ).distinct()
        return queryset

    def get_tag(self, queryset, name, value):
        if value:
            return queryset.filter(
                tags__in=value,
            ).distinct()
        return queryset

    def get_theme(self, queryset, name, value):
        if value:
            return queryset.filter(
                theme__in=value,
            )
        return queryset

    def get_reason(self, queryset, name, value):
        if value:
            return queryset.filter(
                reason__in=value,
            )
        return queryset

    def get_district(self, queryset, name, value):
        if value:
            return queryset.filter(
                address__district__in=value,
            )
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
        OpenApiParameter("district", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("district_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
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
        OpenApiParameter("open_cases", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("page_size", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("postal_code_range", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("priority", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("project", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("project_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("reason", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("reason_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter(
            "schedule_day_segment", OpenApiTypes.NUMBER, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "schedule_from_date_added", OpenApiTypes.DATE, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "schedule_housing_corporation_combiteam",
            OpenApiTypes.BOOL,
            OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            "schedule_visit_from", OpenApiTypes.DATE, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "schedule_week_segment", OpenApiTypes.NUMBER, OpenApiParameter.QUERY
        ),
        OpenApiParameter("sensitive", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("simplified", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("state_types", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("state_types__name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("subject", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("subject_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("tag", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("task", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("theme", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("theme_name", OpenApiTypes.STR, OpenApiParameter.QUERY),
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
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    permission_classes = [(IsInAuthorizedRealm & CanAccessSensitiveCases) | TopKeyAuth]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    filter_backends = (
        filters.DjangoFilterBackend,
        RelatedOrderingFilter,
    )
    ordering_fields = "__all_related__"
    filterset_class = CaseFilter
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        # Send `simplified` as parameter to use a simplified serializer with less details.
        is_simplified = self.request.query_params.get("simplified", False) == "true"
        if is_simplified:
            return CaseSimplifiedSerializer
        if self.action == "retrieve":
            return CaseDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return CaseCreateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if TopKeyAuth().has_permission(self.request, None):
            return queryset
        if (
            self.action in ("list",)
            and hasattr(self.request, "user")
            and not self.request.user.has_perm("users.access_sensitive_dossiers")
        ):
            queryset = queryset.exclude(sensitive=True)
        return queryset

    @action(
        detail=False,
        methods=["get"],
    )
    def count(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        count = queryset.count()
        content = {"count": count}
        return Response(content)

    @extend_schema(
        description="Get all data for cases",
        responses={status.HTTP_200_OK: CaseDataSerializer(many=True)},
    )
    @action(
        detail=False,
        url_path="data",
        methods=["get"],
    )
    def get_cases_data(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        paginator = StandardResultsSetPagination()
        context = paginator.paginate_queryset(queryset, request)
        serializer = CaseDataSerializer(
            context, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Get workflows for this Case",
        responses={status.HTTP_200_OK: CaseWorkflowSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="workflows")
    def get_workflows(self, request, pk):
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
        url_name="processes",
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
        options = WorkflowOption.objects.filter(
            theme=case.theme,
        )
        if case.end_date:
            options = options.filter(
                enabled_on_case_closed=True,
            )

        serializer = WorkflowOptionSerializer(
            options,
            many=True,
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

    @extend_schema(
        description="Gets the DocumentType instances associated with this case",
        responses={status.HTTP_200_OK: DocumentTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="document-types",
        methods=["get"],
    )
    def documents_types(self, request, pk):
        case = self.get_object()
        case_meta = get_open_zaak_case(case.case_url)
        zaaktype_meta = get_zaaktype(case_meta.zaaktype)
        document_types = [
            dt
            for dt in get_document_types()
            if dt.get("url") in zaaktype_meta.informatieobjecttypen
        ]
        serializer = DocumentTypeSerializer(document_types, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Gets the CaseDocument instances associated with this case",
        responses={
            status.HTTP_200_OK: serializers.ListSerializer(
                child=serializers.DictField()
            )
        },
    )
    @action(
        detail=True,
        url_path="documents",
        url_name="documents",
        methods=["get"],
        serializer_class=serializers.ListSerializer(child=serializers.DictField()),
    )
    def documents(self, request, pk):
        paginator = LimitOffsetPagination()
        case = self.get_object()
        document_urls = case.casedocument_set.all().values("document_url", "id")
        documents_ids = {d.get("document_url"): d.get("id") for d in document_urls}
        documents = get_documents_meta([d.get("document_url") for d in document_urls])

        # adds CaseDocument ids to documents from zgw-consumer
        documents = [{**d, "id": documents_ids.get(d.get("url"))} for d in documents]
        context = paginator.paginate_queryset(documents, request)
        return paginator.get_paginated_response(context)

    @extend_schema(
        description="Add CaseDocument instances and associate it with this case",
        responses={status.HTTP_200_OK: CaseDocumentSerializer()},
        request=CaseDocumentUploadSerializer(),
    )
    @parser_classes([JSONParser, FormParser, MultiPartParser])
    @action(
        detail=True,
        url_path="documents/create",
        url_name="documents-create",
        methods=["post"],
        serializer_class=CaseDocumentUploadSerializer,
    )
    def add_document(self, request, pk):
        case = self.get_object()
        file_uploaded = request.FILES.get("file")
        response = create_document(
            case,
            file_uploaded,
            "nld",
            request.data.get("documenttype_url"),
        )
        serialized = CaseDocumentSerializer(response)
        return Response(serialized.data)

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
            queryset.distinct("reason__name")
            .order_by("reason__name")
            .values_list("reason__name", flat=True)
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
            queryset.distinct("address__district__name")
            .order_by("address__district__name")
            .values_list("address__district__name", flat=True)
        )
        serializer = serializers.ListSerializer(queryset, child=serializers.CharField())
        return Response(serializer.data)

    # This is a dedicated endpoint for the data team, provided in support of OOV.
    @extend_schema(
        description="Returns a list of all open cases with their corresponding BAG IDs",
        responses={status.HTTP_200_OK: CaseBagIdsSerializer(many=True)},
    )
    @action(
        detail=False,
        url_path="bag-ids",
        methods=["get"],
        authentication_classes=[ScopedTokenAuth],
        permission_classes=[ScopedViewPermission],
    )
    def bag_ids(self, request):
        queryset = self.get_queryset().filter(end_date__isnull=True)  # Only open cases
        paginator = StandardResultsSetPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = CaseBagIdsSerializer(
            paginated_queryset, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)


class CaseDocumentViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [CanAccessSensitiveCases]
    serializer_class = CaseDocumentSerializer
    queryset = CaseDocument.objects.all()
    pagination_class = StandardResultsSetPagination

    def retrieve(self, request, *args, **kwargs):
        casedocument = self.get_object()
        document = get_document(casedocument.document_url)
        document.update({"id": casedocument.id})
        return Response(document)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_document(instance)
        return super().destroy(request, *args, **kwargs)

    @action(
        detail=True,
        url_path="download",
        methods=["get"],
    )
    def download(self, request, pk):
        casedocument = self.get_object()
        document = get_document(casedocument.document_url)
        content = get_document_inhoud(casedocument.document_content)

        response = FileResponse(io.BytesIO(content))
        response[
            "Content-Disposition"
        ] = f"attachment; filename={document.get('bestandsnaam')}"
        response["Content-Type"] = get_mimetype(document.get("formaat"))
        response["Content-Length"] = document.get("bestandsomvang")
        response["Last-Modified"] = document.get("creatiedatum")
        return response


class DocumentTypeViewSet(viewsets.ViewSet):
    serializer_class = DocumentTypeSerializer

    def list(self, request):
        document_types = get_document_types()
        serializer = self.serializer_class(document_types, many=True)
        return Response(serializer.data)
