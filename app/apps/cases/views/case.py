import io
import mimetypes
import operator
from functools import reduce

from apps.addresses.models import HousingCorporation
from apps.cases.models import Case, CaseDocument, CaseProject, CaseReason, CaseStateType
from apps.cases.serializers import (
    AdvertisementSerializer,
    CaseDocumentSerializer,
    CaseDocumentUploadSerializer,
    CaseSerializer,
    CitizenReportSerializer,
    DocumentTypeSerializer,
    SubjectSerializer,
)
from apps.events.mixins import CaseEventsMixin
from apps.main.filters import RelatedOrderingFilter
from apps.main.pagination import EmptyPagination
from apps.openzaak.helpers import (
    create_document,
    get_case_type,
    get_case_types,
    get_document,
    get_document_inhoud,
    get_document_types,
    get_documents_from_case,
    get_documents_meta,
    get_open_zaak_case,
)
from apps.schedules.models import DaySegment, Priority, Schedule, WeekSegment
from apps.users.permissions import (
    CanAccessSensitiveCases,
    rest_permission_classes_for_top,
)
from apps.workflow.models import CaseWorkflow, WorkflowOption
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
    from_start_date = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    open_cases = filters.BooleanFilter(method="get_open_cases")
    is_enforcement_request = filters.BooleanFilter(
        method="get_enforcement_request_cases"
    )
    state_types = filters.ModelMultipleChoiceFilter(
        queryset=CaseStateType.objects.all(), method="get_state_types"
    )
    schedule_day_segment = filters.ModelMultipleChoiceFilter(
        queryset=DaySegment.objects.all(),
        method="get_schedule_day_segment",
    )
    schedule_week_segment = filters.ModelMultipleChoiceFilter(
        queryset=WeekSegment.objects.all(),
        method="get_schedule_week_segment",
    )
    priority = filters.ModelMultipleChoiceFilter(
        queryset=Priority.objects.all(),
        method="get_schedule_priority",
    )
    schedule_visit_from = filters.DateTimeFilter(
        method="get_schedule_visit_from",
    )
    schedule_from_date_added = filters.DateTimeFilter(
        method="get_schedule_from_date_added",
    )
    schedule_housing_corporation_combiteam = filters.BooleanFilter(
        method="get_schedule_housing_corporation_combiteam"
    )
    state_types__name = filters.ModelMultipleChoiceFilter(
        queryset=CaseStateType.objects.all(),
        method="get_state_types",
        to_field_name="name",
    )
    project = filters.ModelMultipleChoiceFilter(
        queryset=CaseProject.objects.all(), method="get_project"
    )
    reason = filters.ModelMultipleChoiceFilter(
        queryset=CaseReason.objects.all(), method="get_reason"
    )
    ton_ids = CharArrayFilter(field_name="ton_ids", lookup_expr="contains")
    street_name = filters.CharFilter(method="get_fuzy_street_name")
    number = filters.CharFilter(method="get_number")
    housing_corporation = filters.ModelMultipleChoiceFilter(
        queryset=HousingCorporation.objects.all(),
        method="get_housing_corporation",
    )
    suffix = filters.CharFilter(method="get_suffix")
    postal_code = filters.CharFilter(method="get_postal_code")
    postal_code_range = MultipleValueFilter(
        field_class=CharField, method="get_postal_code_range"
    )

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

    def get_fuzy_street_name(self, queryset, name, value):
        return queryset.filter(address__street_name__trigram_similar=value)

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

    def get_project(self, queryset, name, value):
        if value:
            return queryset.filter(
                project__in=value,
            )
        return queryset

    def get_reason(self, queryset, name, value):
        if value:
            return queryset.filter(
                reason__in=value,
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
        OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("from_start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("theme", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("reason", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("sensitive", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter("open_cases", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
        OpenApiParameter(
            "is_enforcement_request", OpenApiTypes.BOOL, OpenApiParameter.QUERY
        ),
        OpenApiParameter("state_types", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter(
            "schedule_day_segment", OpenApiTypes.NUMBER, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "schedule_week_segment", OpenApiTypes.NUMBER, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "schedule_visit_from", OpenApiTypes.DATE, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "schedule_from_date_added", OpenApiTypes.DATE, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "schedule_housing_corporation_combiteam",
            OpenApiTypes.BOOL,
            OpenApiParameter.QUERY,
        ),
        OpenApiParameter("postal_code_range", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("project", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("state_types__name", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("page_size", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("ton_ids", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("priority", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
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
    permission_classes = rest_permission_classes_for_top() + [CanAccessSensitiveCases]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    filter_backends = (
        filters.DjangoFilterBackend,
        RelatedOrderingFilter,
    )
    ordering_fields = "__all_related__"
    filterset_class = CaseFilter
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
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
        zaaktype_meta = get_case_type(case_meta.zaaktype)
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
        methods=["get"],
        serializer_class=serializers.ListSerializer(child=serializers.DictField()),
    )
    def documents(self, request, pk):
        paginator = LimitOffsetPagination()
        case = self.get_object()
        document_urls = case.casedocument_set.all().values_list(
            "document_url", flat=True
        )
        documents = get_documents_meta(document_urls)
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


class CaseDocumentViewSet(
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [CanAccessSensitiveCases]
    serializer_class = CaseDocumentSerializer
    queryset = CaseDocument.objects.all()
    pagination_class = StandardResultsSetPagination

    def retrieve(self, request, *args, **kwargs):
        casedocument = self.get_object()
        document = get_document(casedocument.document_url)
        print(document)
        return Response(document)

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
        ] = f"attachment; filename={document.bestandsnaam}"
        response["Content-Type"] = mimetypes.types_map[document.formaat]
        response["Content-Length"] = document.bestandsomvang
        response["Last-Modified"] = document.creatiedatum
        return response


class DocumentTypeViewSet(viewsets.ViewSet):
    def list(self, request):
        document_types = get_document_types()
        serializer = DocumentTypeSerializer(document_types, many=True)
        return Response(serializer.data)
