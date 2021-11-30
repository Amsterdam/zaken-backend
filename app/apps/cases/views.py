import datetime
import logging
import mimetypes
import os
from collections import OrderedDict

import requests
from apps.addresses.utils import search
from apps.cases.models import (
    Case,
    CaseClose,
    CaseProject,
    CaseReason,
    CaseState,
    CaseTheme,
    CitizenReport,
)
from apps.cases.serializers import (
    BWVMeldingenSerializer,
    BWVStatusSerializer,
    CaseCloseReasonSerializer,
    CaseCloseResultSerializer,
    CaseCloseSerializer,
    CaseCreateUpdateSerializer,
    CaseProjectSerializer,
    CaseReasonSerializer,
    CaseSerializer,
    CaseStateSerializer,
    CaseStateTypeSerializer,
    CaseThemeSerializer,
    CaseWorkflowSerializer,
    CitizenReportSerializer,
    LegacyCaseCreateSerializer,
    LegacyCaseUpdateSerializer,
    PushCaseStateSerializer,
    StartWorkflowSerializer,
)
from apps.cases.swagger_parameters import date as date_parameter
from apps.cases.swagger_parameters import no_pagination as no_pagination_parameter
from apps.cases.swagger_parameters import open_cases as open_cases_parameter
from apps.cases.swagger_parameters import open_status as open_status_parameter
from apps.cases.swagger_parameters import postal_code as postal_code_parameter
from apps.cases.swagger_parameters import reason as reason_parameter
from apps.cases.swagger_parameters import start_date as start_date_parameter
from apps.cases.swagger_parameters import street_name as street_name_parameter
from apps.cases.swagger_parameters import street_number as street_number_parameter
from apps.cases.swagger_parameters import suffix as suffix_parameter
from apps.cases.swagger_parameters import theme as theme_parameter
from apps.debriefings.models import Debriefing
from apps.debriefings.serializers import ViolationTypeSerializer
from apps.decisions.serializers import DecisionTypeSerializer
from apps.events.mixins import CaseEventsMixin
from apps.schedules.serializers import ThemeScheduleTypesSerializer
from apps.summons.serializers import SummonTypeSerializer
from apps.users.models import User
from apps.users.permissions import (
    CanCloseCase,
    CanCreateCase,
    rest_permission_classes_for_top,
)
from apps.visits.models import Visit
from apps.visits.serializers import VisitSerializer
from apps.workflow.models import CaseWorkflow, GenericCompletedTask, WorkflowOption
from apps.workflow.serializers import (
    GenericCompletedTaskSerializer,
    WorkflowOptionSerializer,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.edit import FormView
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from utils.api_queries_bag import do_bag_search_address_exact

from .forms import ImportBWVCaseDataForm

logger = logging.getLogger(__name__)


class CaseStateViewSet(viewsets.ViewSet):
    """
    Pushes the case state
    """

    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseStateSerializer
    queryset = CaseState.objects.all()

    @action(
        detail=True,
        url_path="update-from-top",
        methods=["post"],
        serializer_class=PushCaseStateSerializer,
    )
    def update_from_top(self, request, pk):
        logger.info("Receiving pushed state update")
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            logger.error("Serializer error: {serializer.errors}")
            raise APIException(f"Serializer error: {serializer.errors}")

        try:
            case_state = CaseState.objects.get(id=pk)
            case_state.users.clear()
            user_emails = data.get("user_emails", [])
            logger.info(f"Updating CaseState {len(user_emails)} users")
            user_model = get_user_model()

            for user_email in user_emails:
                user_object, _ = user_model.objects.get_or_create(email=user_email)
                case_state.users.add(user_object)
                logger.info("Added user to CaseState")

            return Response(CaseStateSerializer(case_state).data)
        except Exception as e:
            logger.error(f"Could not process push data: {e}")
            raise logger(f"Could not push data: {e}")


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

    @extend_schema(
        parameters=[
            date_parameter,
            start_date_parameter,
            open_cases_parameter,
            theme_parameter,
            reason_parameter,
            open_status_parameter,
            no_pagination_parameter
        ],
        description="Case filter query parameters",
        responses={200: CaseSerializer(many=True)},
    )
    def list(self, request):
        date = request.GET.get(date_parameter.name, None)
        start_date = request.GET.get(start_date_parameter.name, None)
        open_cases = request.GET.get(open_cases_parameter.name, None)
        theme = request.GET.get(theme_parameter.name, None)
        reason = request.GET.get(reason_parameter.name, None)
        open_status = request.GET.get(open_status_parameter.name, None)
        no_pagination = request.GET.get(no_pagination_parameter.name, None)

        queryset = self.get_queryset()

        if date:
            queryset = queryset.filter(start_date=date)
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if open_cases:
            open_cases = open_cases == "true"
            queryset = queryset.filter(end_date__isnull=open_cases)
        if theme:
            queryset = queryset.filter(theme=theme)
        if reason:
            queryset = queryset.filter(reason=reason)
        if open_status:
            queryset = queryset.filter(
                case_states__end_date__isnull=True,
                case_states__status__id__in=open_status.split(","),
            ).distinct()

        if no_pagination == "true":
            serializer = CaseSerializer(queryset, many=True)
            return Response(serializer.data)

        paginator = LimitOffsetPagination()
        context = paginator.paginate_queryset(queryset, request)
        serializer = CaseSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        parameters=[
            postal_code_parameter,
            street_number_parameter,
            street_name_parameter,
            suffix_parameter,
            theme_parameter,
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

        if postal_code is None and street_name is None:
            return HttpResponseBadRequest(
                "A postal_code or street_name queryparameter should be provided"
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

        paginator = PageNumberPagination()
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
        serializer = CaseWorkflowSerializer(context, many=True, context={"request": request})
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


class CaseThemeViewSet(ListAPIView, viewsets.ViewSet):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseThemeSerializer
    queryset = CaseTheme.objects.all()

    @extend_schema(
        description="Gets the reasons associated with the requested theme",
        responses={status.HTTP_200_OK: CaseReasonSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="reasons",
        methods=["get"],
    )
    def reasons(self, request, pk):
        paginator = PageNumberPagination()
        theme = self.get_object()
        query_set = theme.reasons.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseReasonSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the SummonTypes associated with the given theme",
        responses={status.HTTP_200_OK: SummonTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="summon-types",
        methods=["get"],
    )
    def summon_types(self, request, pk):
        paginator = PageNumberPagination()
        theme = self.get_object()
        query_set = theme.summon_types.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = SummonTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the DecisionTypes associated with the given theme",
        responses={status.HTTP_200_OK: DecisionTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="decision-types",
        methods=["get"],
    )
    def decision_types(self, request, pk):
        paginator = PageNumberPagination()
        theme = self.get_object()
        query_set = theme.decision_types.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = DecisionTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the Scheduling Types associated with the given theme",
        responses={status.HTTP_200_OK: ThemeScheduleTypesSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="schedule-types",
        methods=["get"],
    )
    def schedule_types(self, request, pk):
        theme = self.get_object()
        serializer = ThemeScheduleTypesSerializer(theme)
        return Response(serializer.data)

    @extend_schema(
        description="Gets the CaseStateTypes associated with the given theme",
        responses={status.HTTP_200_OK: CaseStateTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="state-types",
        methods=["get"],
    )
    def state_types(self, request, pk):
        paginator = PageNumberPagination()
        theme = self.get_object()
        query_set = theme.state_types.all()
        if request.GET.get("role") == "toezichthouder":
            query_set = query_set.filter(
                id__in=theme.case_state_types_top.values_list("id", flat=True)
            )

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseStateTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the ViolationTypes",
        responses={status.HTTP_200_OK: ViolationTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="violation-types",
        methods=["get"],
    )
    def violation_types(self, request, pk):
        paginator = PageNumberPagination()
        types = [{"key": t[0]} for t in Debriefing.VIOLATION_CHOICES]
        context = paginator.paginate_queryset(types, request)
        serializer = ViolationTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the CaseCloseReasons associated with the given theme",
        responses={status.HTTP_200_OK: CaseCloseReasonSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="case-close-reasons",
        methods=["get"],
    )
    def case_close_reasons(self, request, pk):
        paginator = PageNumberPagination()
        theme = self.get_object()
        query_set = theme.caseclosereason_set.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseCloseReasonSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the CaseProjects associated with the given theme",
        responses={status.HTTP_200_OK: CaseProjectSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="case-projects",
        methods=["get"],
    )
    def case_projects(self, request, pk):
        paginator = PageNumberPagination()
        theme = self.get_object()
        query_set = theme.caseproject_set.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseProjectSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the CaseCloseResult associated with the given theme",
        responses={status.HTTP_200_OK: CaseCloseResultSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="case-close-results",
        methods=["get"],
    )
    def case_close_results(self, request, pk):
        paginator = PageNumberPagination()
        theme = self.get_object()
        query_set = theme.casecloseresult_set.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseCloseResultSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)


@user_passes_test(lambda u: u.is_superuser)
def download_data(request):
    DATABASE_USER = os.environ.get("DATABASE_USER")
    DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
    DATABASE_HOST = os.environ.get("DATABASE_HOST")
    DATABASE_NAME = os.environ.get("DATABASE_NAME")

    filename = "zaken_db.sql"

    command = f"PGPASSWORD='{DATABASE_PASSWORD}' pg_dump -U {DATABASE_USER} -d {DATABASE_NAME} -h {DATABASE_HOST} > {filename}"
    os.system(command)

    fl_path = "/app/"

    fl = open(os.path.join(fl_path, filename), "r")
    mime_type, _ = mimetypes.guess_type(fl_path)
    response = HttpResponse(fl, content_type=mime_type)
    response["Content-Disposition"] = "attachment; filename=%s" % filename
    return response


class ImportBWVCaseDataView(UserPassesTestMixin, FormView):
    form_class = ImportBWVCaseDataForm
    template_name = "import/body.html"

    reason_translate = {
        "melding": "Melding",
        "project": "Project",
        "digitaal_toezicht": "Digitaal Toezicht",
    }
    label_translate = {
        "HM_DATE_CREATED": "Datum aangemaakt",
        "WS_DATE_CREATED": "Datum aangemaakt",
        "WS_DATE_MODIFIED": "Datum aangepast",
        "HM_DATE_MODIFIED": "Datum aangepast",
        "HM_USER_CREATED": "Aangemaakt door",
        "WS_USER_CREATED": "Aangemaakt door",
        "HM_USER_MODIFIED": "Aangepast door",
        "WS_USER_MODIFIED": "Aangepast door",
        "HM_SITUATIE_SCHETS": "Situatieschets",
        "WS_STA_CD_OMSCHRIJVING": "Stadium naam",
        "HM_MELDER_TELNR": "Melder telefoonnummer",
        "HB_OPMERKING": "Huisbezoek opmerking",
        "HB_HIT": "Huisbezoek hit",
        "HB_TOEZ_HDR1_CODE": "Huisbezoek toezichthouder 1",
        "HB_TOEZ_HDR2_CODE": "Huisbezoek toezichthouder 2",
        "HB_BEVINDING_DATUM": "Huisbezoek datum",
        "HB_BEVINDING_TIJD": "Huisbezoek tijd",
    }

    def translate_key_to_label(self, key):
        label = self.label_translate.get(key)
        if label:
            return label
        else:
            label = key
        if label.find("_", 0, 3) >= 0:
            label = label.split("_", 1)[1]
        return label.lower().replace("_", " ").capitalize()

    def _add_address(self, data):
        address_mismatches = []
        results = []
        for d in data:
            bag_result = do_bag_search_address_exact(d).get("results", [])
            bag_result = [r for r in bag_result]

            d_clone = dict(d)
            if bag_result:
                d_clone["address"] = {
                    "bag_id": bag_result[0]["adresseerbaar_object_id"]
                }
                results.append(d_clone)
            else:
                address_mismatches.append({"data": d_clone, "address": bag_result})

        return results, address_mismatches

    def _get_headers(self, auth_header=None):
        token = settings.SECRET_KEY_AZA_TOP
        headers = {
            "Authorization": f"{auth_header}" if auth_header else f"{token}",
            "content-type": "application/json",
        }
        return headers

    def _fetch_visit(self, legacy_bwv_case_id):
        url = f"{settings.TOP_API_URL}/cases/{legacy_bwv_case_id}/visits/"
        try:
            response = requests.get(
                url=url,
                headers=self._get_headers(),
                timeout=5,
            )
            response.raise_for_status()
        except Exception:
            return response.status_code
        else:
            return response.json()

    def _add_visits(self, data, *args, **kwargs):
        errors = []
        if settings.TOP_API_URL and settings.SECRET_KEY_AZA_TOP:
            for d in data:
                visits = self._fetch_visit(d["legacy_bwv_case_id"])

                if isinstance(visits, list):
                    for visit in visits:
                        visit["authors"] = [
                            tm.get("user", {}) for tm in visit.get("team_members", [])
                        ]
                    d["visits"] = visits
                else:
                    errors.append(
                        {
                            "legacy_bwv_case_id": d["legacy_bwv_case_id"],
                            "status_code": visits,
                        }
                    )
        return data, errors

    def add_theme(self, data, *args, **kwargs):
        theme = CaseTheme.objects.get(id=kwargs.get("theme"))
        used_theme_instances = {
            "reasons": [],
            "projects": [],
        }
        missing_themes = []
        for d in data:
            reason = CaseReason.objects.filter(
                name=self.reason_translate.get(d.get("reason")),
                theme=theme,
            ).first()
            project = CaseProject.objects.filter(
                name=d["project"],
                theme=theme,
            ).first()
            if reason and project:
                d["reason"] = reason.id
                d["project"] = project.id
                d["theme"] = theme.id
                used_theme_instances["reasons"].append(reason)
                used_theme_instances["projects"].append(project)
            else:
                d["theme"] = "not_found"
                missing_themes.append(
                    {
                        "legacy_bwv_case_id": d["legacy_bwv_case_id"],
                        "reason": reason,
                        "reason_found": d["reason"],
                        "project": project,
                        "project_found": d["project"],
                    }
                )
        data = [d for d in data if d.get("theme") != "not_found"]
        return data, missing_themes, used_theme_instances

    def add_status_name(self, data, *args, **kwargs):
        status_name = kwargs.get("status_name")
        if status_name:
            for d in data:
                d["status_name"] = status_name
        return data

    def _get_object(self, case_id):
        return Case.objects.filter(
            legacy_bwv_case_id=case_id, is_legacy_bwv=True
        ).first()

    def _create_or_update(
        self, data, request, commit, user=None, reasons=[], projects=[], kwargs={}
    ):
        theme = CaseTheme.objects.get(id=kwargs.get("theme"))
        melding = CaseReason.objects.get(
            name=settings.DEFAULT_REASON,
            theme=theme,
        )
        errors = []
        results = []
        context = {"request": request}
        for d in data:
            d_clone = dict(d)
            instance = self._get_object(d.get("legacy_bwv_case_id"))

            if d["reason"] == melding.id:
                del d["project"]

            if instance:
                serializer = self.get_serializer(instance, data=d, context=context)
            else:
                serializer = self.get_serializer(data=d, context=context)

            if serializer.is_valid(raise_exception=True):
                d_clone.update(
                    {
                        "case": d.get("legacy_bwv_case_id"),
                        "created": False if instance else True,
                    }
                )
                if commit:
                    if d["reason"] in reasons:
                        if d["reason"] != melding.id and d["project"] not in projects:
                            continue
                    else:
                        continue

                    case = serializer.save()
                    if user:
                        case.author = user
                        case.save()
                    d_clone["case"] = case.id

                    # create visits, no update
                    for visit in d.get("visits", []):
                        visit["case"] = case.id
                        visit["task"] = "-1"
                        visit_instances = Visit.objects.filter(
                            case=case,
                            start_time=visit.get("start_time"),
                            situation=visit.get("situation"),
                            observations=visit.get("observations"),
                            can_next_visit_go_ahead=visit.get(
                                "can_next_visit_go_ahead"
                            ),
                            can_next_visit_go_ahead_description=visit.get(
                                "can_next_visit_go_ahead_description"
                            ),
                            suggest_next_visit=visit.get("suggest_next_visit"),
                            suggest_next_visit_description=visit.get(
                                "suggest_next_visit_description"
                            ),
                            notes=visit.get("notes"),
                        )

                        visit_serializer = VisitSerializer(data=visit)
                        if visit_serializer.is_valid() and not visit_instances:
                            visit_serializer.save()
                        else:
                            logger.info(f"Visit serializer errors, case '{case.id}'")
                            logger.info(visit_serializer.errors)

                results.append(d_clone)
            else:
                errors.append(
                    {
                        "legacy_bwv_case_id": d.get("legacy_bwv_case_id"),
                        "errors": serializer.errors,
                    }
                )
        return errors, results

    def create_additional_types(self, result_data, user=None, *args, **kwargs):
        errors = []
        for d in result_data:
            events = d["meldingen"] + d["geschiedenis"]
            case = d["case"]
            events = [
                dict(
                    e,
                    date_added=datetime.datetime.strptime(e["date_added"], "%d-%m-%Y"),
                    case_user_task_id="-1",
                    author=user.id,
                    case=d["case"],
                )
                for e in events
            ]

            events_sorted = sorted(events, key=lambda d: d.get("date_added"))

            without_existing_events = [
                e
                for e in events_sorted
                if not GenericCompletedTask.objects.filter(
                    case__id=d.get("case"),
                    description=e.get("description"),
                )
            ]
            events_serializer = GenericCompletedTaskSerializer(
                data=without_existing_events,
                context={"request": self.request},
                many=True,
            )
            if events_serializer.is_valid():
                events_instances = events_serializer.save()
                for e in events_instances:
                    e.author = user
                    try:
                        date_added = dict(
                            (
                                ee.get("variables", {}).get("bwv_id"),
                                ee.get("date_added"),
                            )
                            for ee in events
                        ).get(e.variables.get("bwv_id"))
                        e.date_added = date_added
                    except Exception:
                        pass
                    e.save()
            else:
                logger.info(f"GenericCompletedTaskSerializer errors: case '{case}'")
                logger.info(events_serializer.errors)
        return errors, result_data

    def _parse_case_data_to_case_serializer(self, data):
        map = {
            "WV_DATE_CREATED": "start_date",
            "WV_MEDEDELINGEN": "description",
            "ADS_PSCD": "postcode",
            "ADS_HSNR": "huisnummer",
            "ADS_HSLT": "huisletter",
            "ADS_HSTV": "toev",
            "CASE_REASON": "reason",
            "WV_BEH_CD_OMSCHRIJVING": "project",
        }

        def to_int(v):

            try:
                v = int(v.strip().split(".")[0])
            except Exception:
                pass
            return v

        transform = {
            "huisnummer": to_int,
        }

        def clean(value, key):
            value = value.strip() if isinstance(value, str) else value
            value = value if not transform.get(key) else transform.get(key)(value)
            try:
                value = datetime.datetime.strptime(value, "%d-%m-%Y").strftime(
                    "%Y-%m-%d"
                )
            except Exception:
                pass
            return value

        return [
            dict((map.get(k, k), clean(v, map.get(k, k))) for k, v in d.items())
            for d in data
        ]

    def get_success_url(self, **kwargs):
        return reverse(kwargs.get("url_name"))

    @property
    def get_serializer(self):
        return LegacyCaseCreateSerializer

    def _add_bwv_meldingen(self, data):
        for d in data:
            additionals_list_items = d.get("meldingen", {}).get("meldingen", {})
            d["meldingen"] = []
            case = d.get("legacy_bwv_case_id")
            if additionals_list_items:
                additionals_list = [v for k, v in additionals_list_items.items()]
                additionals_serializer = BWVMeldingenSerializer(
                    data=additionals_list, many=True
                )
                if additionals_serializer.is_valid():
                    sorted_data = sorted(
                        additionals_serializer.data,
                        key=lambda d: d.get("WS_DATE_CREATED"),
                    )

                    validated_data = []
                    for status_variables in sorted_data:
                        mapped_form_data = OrderedDict(
                            (
                                f"{list(status_variables.keys()).index(k):02}{k}",
                                {
                                    "label": self.translate_key_to_label(k),
                                    "value": v,
                                },
                            )
                            for k, v in status_variables.items()
                        )
                        status_data = OrderedDict(
                            {
                                "description": f"BWV Melding: {status_variables.get('HOTLINE_MELDING_ID')}",
                                "variables": OrderedDict(
                                    {
                                        "mapped_form_data": mapped_form_data,
                                        "bwv_id": status_variables.get(
                                            "HOTLINE_MELDING_ID"
                                        ),
                                    }
                                ),
                                "date_added": status_variables.get("HM_DATE_CREATED"),
                            }
                        )

                        validated_data.append(status_data)

                    d["meldingen"] = validated_data
                else:
                    logger.info(f"BWVMeldingenSerializer errors: case '{case}'")
                    logger.info(additionals_serializer.errors)

        return data

    def _add_bwv_status(self, data):
        for d in data:
            case = d.get("legacy_bwv_case_id")
            bwv_status_items = d.get("geschiedenis", {}).get("history", {})
            d["geschiedenis"] = []
            if bwv_status_items:

                generic_completed_task_list = [v for k, v in bwv_status_items.items()]

                status_serializer = BWVStatusSerializer(
                    data=generic_completed_task_list, many=True
                )

                if status_serializer.is_valid():
                    sorted_data = sorted(
                        status_serializer.data, key=lambda d: d.get("WS_DATE_CREATED")
                    )

                    validated_status_data = []
                    for status_variables in sorted_data:
                        mapped_form_data = OrderedDict(
                            (
                                f"{list(status_variables.keys()).index(k):02}{k}",
                                {
                                    "label": self.translate_key_to_label(k),
                                    "value": v,
                                },
                            )
                            for k, v in status_variables.items()
                        )
                        status_data = {
                            "description": f"BWV Status: {status_variables.get('WS_STA_CD_OMSCHRIJVING')}",
                            "variables": {
                                "mapped_form_data": mapped_form_data,
                                "bwv_id": status_variables.get("STADIUM_ID"),
                            },
                            "date_added": status_variables.get("WS_DATE_CREATED"),
                        }

                        validated_status_data.append(status_data)

                    d["geschiedenis"] = validated_status_data
                else:
                    logger.info(f"BWVStatusSerializer errors: case '{case}'")
                    logger.info(status_serializer.errors)

        return data

    def add_parsed_data(self, data, *args, **kwargs):
        data, visit_errors = self._add_visits(data, *args, **kwargs)
        data, missing_themes, used_theme_instances = self.add_theme(
            data, *args, **kwargs
        )
        data = self.add_status_name(data, *args, **kwargs)
        data = self._add_bwv_meldingen(data)
        data = self._add_bwv_status(data)
        return data, visit_errors, missing_themes, used_theme_instances

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        create_update_results = []
        if request.GET.get("commit"):
            data = self.request.session.get("validated_cases_data")
            form_data = self.request.session.get("validated_cases_data_form_data")
            reasons = [int(id) for id in request.GET.getlist("reason", [])]
            projects = [int(id) for id in request.GET.getlist("project", [])]
            kwargs.update(form_data)

            user = kwargs.get("user")
            if user:
                user = User.objects.get(id=user)
            if data:
                create_update_errors, create_update_results = self._create_or_update(
                    data,
                    request,
                    True,
                    user,
                    reasons,
                    projects,
                    kwargs,
                )
                (
                    create_additionals_errors,
                    create_additionals_results,
                ) = self.create_additional_types(
                    create_update_results,
                    user,
                )
                del self.request.session["validated_cases_data"]
                del self.request.session["validated_cases_data_form_data"]
            else:
                return redirect(reverse("import-bwv-cases"))
            context.update(
                {
                    "commited": True,
                    "create_update_results": create_update_results,
                }
            )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(**kwargs)
        data = (
            original_data
        ) = (
            address_mismatches
        ) = (
            create_update_errors
        ) = create_update_results = visit_errors = missing_themes = []
        used_theme_instances = {}
        form_valid = False

        if form.is_valid():
            original_data = form.cleaned_data["json_data"]
            form_data = dict(
                (k, str(v.id) if hasattr(v, "id") else v)
                for k, v in form.cleaned_data.items()
                if k
                in [
                    "user",
                    "project",
                    "reason",
                    "theme",
                    "status_name",
                ]
            )
            kwargs.update(form_data)

            data = self._parse_case_data_to_case_serializer(original_data)
            data, address_mismatches = self._add_address(data)
            (
                data,
                visit_errors,
                missing_themes,
                used_theme_instances,
            ) = self.add_parsed_data(data, *args, **kwargs)
            used_theme_instances["reasons"] = list(set(used_theme_instances["reasons"]))
            used_theme_instances["projects"] = list(
                set(used_theme_instances["projects"])
            )

            create_update_errors, create_update_results = self._create_or_update(
                data,
                request,
                False,
                kwargs.get("user"),
                kwargs=kwargs,
            )
            form_valid = True
            self.request.session["validated_cases_data"] = create_update_results
            self.request.session["validated_cases_data_form_data"] = form_data
        else:
            logger.info("bwv import errors")
            logger.info(form.errors)

        context.update(
            {
                "validation_form_valid": form_valid,
                "data": data,
                "original_data": original_data,
                "address_mismatches": address_mismatches,
                "create_update_errors": create_update_errors,
                "create_update_results": create_update_results,
                "visit_errors": visit_errors,
                "missing_themes": missing_themes,
                "used_theme_instances": used_theme_instances,
            }
        )
        return self.render_to_response(context)


class CaseCloseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = rest_permission_classes_for_top()
    serializer_class = CaseCloseSerializer
    queryset = CaseClose.objects.all()

    def get_permissions(self):
        if self.request.method not in SAFE_METHODS:
            self.permission_classes.append(CanCloseCase)
        return super(CaseCloseViewSet, self).get_permissions()
