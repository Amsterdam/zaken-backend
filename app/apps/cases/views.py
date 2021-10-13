import datetime
import logging

import requests
from apps.addresses.utils import search
from apps.camunda.models import CamundaProcess
from apps.camunda.serializers import (
    CamundaProcessSerializer,
    CamundaTaskSerializer,
    CamundaTaskWithStateSerializer,
)
from apps.cases.models import (
    Case,
    CaseClose,
    CaseCloseReason,
    CaseCloseResult,
    CaseProcessInstance,
    CaseProject,
    CaseReason,
    CaseState,
    CaseStateType,
    CaseTheme,
    CitizenReport,
)
from apps.cases.serializers import (
    CamundaStartProcessSerializer,
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
from apps.workflow.models import CaseWorkflow
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseBadRequest
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
from rest_framework.pagination import PageNumberPagination
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
    queryset = Case.objects.filter(is_legacy_camunda=False)

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
            no_pagination_parameter,
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

        paginator = PageNumberPagination()
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

        serializer = CaseWorkflowSerializer(
            CaseWorkflow.objects.filter(
                case=case, tasks__isnull=False, tasks__completed=False
            ).distinct(),
            many=True,
            context={"request": request},
        )

        return Response(serializer.data)

    @extend_schema(
        description="Get Camunda processes for this Case",
        responses={status.HTTP_200_OK: CamundaProcessSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="processes",
        methods=["get"],
        serializer_class=CamundaProcessSerializer,
    )
    def get_camunda_processes(self, request, pk):
        """
        Get camunda processes for this case. Currently this case detail linking
        does not do anything. This is future proofing this rest call so that we can
        show and not show processes based on the current state of the case
        (for example not show the summon/aanschrijving process when we are in visit state)
        """
        case = get_object_or_404(Case, pk=pk)
        serializer = CamundaProcessSerializer(
            CamundaProcess.objects.filter(theme=case.theme), many=True
        )
        return Response(serializer.data)

    @extend_schema(
        description="Start a process in Camunda",
    )
    @action(
        detail=True,
        url_path="processes/start",
        methods=["post"],
        serializer_class=CamundaStartProcessSerializer,
    )
    def start_process(self, request, pk):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            case = self.get_object()
            instance = data["camunda_process_id"]

            workflow_type = CaseWorkflow.WORKFLOW_TYPE_SUB
            if instance.to_directing_proccess:
                workflow_type = CaseWorkflow.WORKFLOW_TYPE_DIRECTOR

            workflow_instance = CaseWorkflow.objects.create(
                case=case,
                workflow_type=workflow_type,
                workflow_message_name=instance.camunda_message_name,
            )
            workflow_instance.start()

            return Response(
                data=f"Process has started {str(instance)}",
                status=status.HTTP_200_OK,
            )

            # if instance.to_directing_proccess:
            #     response = CamundaService().send_message_to_process_instance(
            #         message_name=instance.camunda_message_name,
            #         process_instance_id=case.directing_process,
            #     )
            # else:
            #     case_process_instance = CaseProcessInstance.objects.create(case=case)
            #     case_process_id = case_process_instance.process_id.__str__()

            #     response = CamundaService().send_message(
            #         message_name=instance.camunda_message_name,
            #         case_identification=case.id,
            #         case_process_id=case_process_id,
            #     )

            #     try:
            #         json_response = response.json()[0]
            #         camunda_process_id = json_response["processInstance"]["id"]
            #     except Exception:
            #         return Response(
            #             data=f"Camunda process has not started. Json response not valid {str(response.content)}",
            #             status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            #         )

            #     case_process_instance.camunda_process_id = camunda_process_id
            #     case_process_instance.save()

            # if response:
            #     return Response(
            #         data=f"Process has started {str(response.content)}",
            #         status=status.HTTP_200_OK,
            #     )
            # else:
            #     return Response(
            #         data=f"Camunda process has not started. Camunda request failed: {response}",
            #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            #     )

        return Response(
            data="Camunda process has not started. serializer not valid",
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


class ImportBWVCaseDataView(UserPassesTestMixin, FormView):
    form_class = ImportBWVCaseDataForm
    template_name = "import/body.html"

    def _map_bag_result_to_address(self, address):
        map = {
            "adresseerbaar_object_id": "bag_id",
        }
        return dict((map.get(k, k), v) for k, v in address.items())

    def _add_address(self, data):
        address_mismatches = []
        results = []
        for d in data:
            bag_result = do_bag_search_address_exact(d).get("results", [])
            bag_result = [
                r
                for r in bag_result
                if not d.get("OBJ_NR_VRA")
                or r["adresseerbaar_object_id"] == "0%s" % d.get("OBJ_NR_VRA")
            ]

            d_clone = dict(d)
            if bag_result:
                d_clone["address"] = {
                    "bag_id": bag_result[0]["adresseerbaar_object_id"]
                }
                results.append(d_clone)
            else:
                address_mismatches.append({"data": d_clone, "address": bag_result})

        return results, address_mismatches

    def _add_theme(self, data, *args, **kwargs):
        theme = get_object_or_404(CaseTheme, name=kwargs.get("theme_name"))
        for d in data:
            d["theme"] = theme.id
        return data

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

    def add_reason(self, data, *args, **kwargs):
        raise NotImplementedError("Case needs a reason")

    def _get_object(self, case_id):
        return Case.objects.filter(
            legacy_bwv_case_id=case_id, is_legacy_bwv=True
        ).first()

    def _create_or_update(self, data, request, commit, user=None):
        errors = []
        results = []
        context = {"request": request}
        for d in data:
            d_clone = dict(d)
            instance = self._get_object(d.get("legacy_bwv_case_id"))
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
                    case = serializer.save()
                    if user:
                        case.author = user
                        case.save()
                    d_clone["case"] = case.id

                    # create visits, no update
                    for visit in d.get("visits", []):
                        visit["case"] = case.id
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

                results.append(d_clone)
            else:
                errors.append(
                    {
                        "legacy_bwv_case_id": d.get("legacy_bwv_case_id"),
                        "errors": serializer.errors,
                    }
                )
        return errors, results

    def create_additional_types(self, result_data, *args, **kwargs):
        errors = []
        return errors, result_data

    def _parse_case_data_to_case_serializer(self, data):
        map = {
            "date_created_zaak": "start_date",
            "mededelingen": "description",
        }

        def clean(value):
            value = value.strip() if isinstance(value, str) else value
            try:
                value = datetime.datetime.strptime(value, "%d-%m-%Y").strftime(
                    "%Y-%m-%d"
                )
            except Exception:
                pass
            return value

        return [dict((map.get(k, k), clean(v)) for k, v in d.items()) for d in data]

    def get_success_url(self, **kwargs):
        return reverse(kwargs.get("url_name"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"theme": get_object_or_404(CaseTheme, name=kwargs.get("theme_name"))}
        )
        return context

    @property
    def get_serializer(self):
        return LegacyCaseCreateSerializer

    def add_parsed_data(self, data, *args, **kwargs):
        data = self._add_theme(data, *args, **kwargs)
        data, visit_errors = self._add_visits(data, *args, **kwargs)
        data = self.add_reason(data, *args, **kwargs)
        return data, visit_errors

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        create_update_results = []
        if request.GET.get("commit"):
            data = self.request.session.get("validated_cases_data")
            user = self.request.session.get("validated_cases_data_user")
            if user:
                user = User.objects.get(id=user)
            if data:
                create_update_errors, create_update_results = self._create_or_update(
                    data,
                    request,
                    True,
                    user,
                )
                (
                    create_additionals_errors,
                    create_additionals_results,
                ) = self.create_additional_types(
                    create_update_results,
                    user,
                )
                del self.request.session["validated_cases_data"]
                del self.request.session["validated_cases_data_user"]
            else:
                return redirect(reverse(context.get("url_name")))
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
        ) = create_update_errors = create_update_results = visit_errors = []
        form_valid = False

        if form.is_valid():
            original_data = form.cleaned_data["json_data"]
            user = form.cleaned_data["user"]

            data = self._parse_case_data_to_case_serializer(original_data)
            data, address_mismatches = self._add_address(data)

            data, visit_errors = self.add_parsed_data(data, *args, **kwargs)

            create_update_errors, create_update_results = self._create_or_update(
                data,
                request,
                False,
                user,
            )
            form_valid = True
            self.request.session["validated_cases_data"] = create_update_results
            self.request.session["validated_cases_data_user"] = str(user.id)

        context.update(
            {
                "validation_form_valid": form_valid,
                "data": data,
                "original_data": original_data,
                "address_mismatches": address_mismatches,
                "create_update_errors": create_update_errors,
                "create_update_results": create_update_results,
                "visit_errors": visit_errors,
            }
        )
        return self.render_to_response(context)


class CaseThemeCitizenReportViewSet(ImportBWVCaseDataView):
    def add_reason(self, data, *args, **kwargs):
        reason, _ = CaseReason.objects.get_or_create(name=settings.DEFAULT_REASON)
        for d in data:
            d["reason"] = reason.id
        return data

    def _add_citizen_report(self, data):
        for d in data:
            d["citizen_report"] = {
                "description_citizenreport": d.get("situatie_schets"),
                "reporter_name": d.get("melder_naam"),
                "reporter_phone": d.get("melder_telnr"),
                "reporter_email": d.get("melder_emailadres"),
                "identification": 1,
            }
        return data

    def create_additional_types(self, result_data, user=None, *args, **kwargs):
        errors = []
        for d in result_data:
            citizen_report = d.get("citizen_report", {})
            citizen_report["case"] = d["case"]
            instances = CitizenReport.objects.filter(
                case__id=d.get("case"), **citizen_report
            )
            serializer = CitizenReportSerializer(
                data=citizen_report, context={"request": self.request}
            )
            if serializer.is_valid() and not instances:
                citizen_report_instance = serializer.save()
                if user:
                    citizen_report_instance.author = user
                    citizen_report_instance.save()
        return errors, result_data

    def add_parsed_data(self, data, *args, **kwargs):
        data, visit_errors = super().add_parsed_data(data, *args, **kwargs)
        data = self._add_citizen_report(data)
        return data, visit_errors


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
