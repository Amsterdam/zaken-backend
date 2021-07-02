import datetime
import logging

from apps.addresses.utils import search
from apps.camunda.models import CamundaProcess
from apps.camunda.serializers import (
    CamundaProcessSerializer,
    CamundaTaskSerializer,
    CamundaTaskWithStateSerializer,
)
from apps.camunda.services import CamundaService
from apps.cases.mock import mock
from apps.cases.models import (
    Case,
    CaseClose,
    CaseCloseReason,
    CaseCloseResult,
    CaseProcessInstance,
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
    CaseReasonSerializer,
    CaseSerializer,
    CaseStateSerializer,
    CaseStateTypeSerializer,
    CaseThemeSerializer,
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
from apps.users.auth_apps import TopKeyAuth
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.edit import FormView
from drf_spectacular.utils import extend_schema
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from utils.api_queries_bag import do_bag_search_address_exact

from .forms import ImportBWVCaseDataForm

logger = logging.getLogger(__name__)


class CaseStateViewSet(viewsets.ViewSet):
    """
    Pushes the case state
    """

    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
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
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = self.perform_create(serializer)

        citizen_report_data = {"case": case.id}
        citizen_report_data.update(request.data)
        citizen_report_serializer = CitizenReportSerializer(data=citizen_report_data)
        if citizen_report_serializer.is_valid():
            citizen_report_serializer.save(author=self.request.user)

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

    @action(detail=False, methods=["post"], url_path="generate-mock")
    def mock_cases(self, request):
        try:
            assert (
                settings.DEBUG or settings.ENVIRONMENT == "acceptance"
            ), "Incorrect enviroment"
            mock()
        except Exception as e:
            return Response(data={"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        description="Get Camunda tasks for this Case",
        responses={status.HTTP_200_OK: CamundaTaskWithStateSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="tasks")
    def get_tasks(self, request, pk):
        case = self.get_object()
        camunda_tasks = []

        for state in case.case_states.filter(end_date__isnull=True):
            tasks = CamundaService().get_all_tasks_by_instance_id(state.case_process_id)
            camunda_tasks.extend([{"state": state, "tasks": tasks}])

        tasks = []
        for camunda_id in case.camunda_ids:
            tasks.extend(CamundaService().get_all_tasks_by_instance_id(camunda_id))

        if len(tasks):
            case_state, _ = CaseStateType.objects.get_or_create(
                name="Geen Status", theme=case.theme
            )
            state = CaseState(
                case=case, status=case_state, start_date=datetime.date.today()
            )
            camunda_tasks.extend([{"state": state, "tasks": tasks}])

        # Camunda tasks can be an empty list or boolean. TODO: This should just be one datatype
        if camunda_tasks is False:
            return Response(
                "Camunda service is offline",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = CamundaTaskWithStateSerializer(camunda_tasks, many=True)
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
        serializer = CamundaProcessSerializer(CamundaProcess.objects.all(), many=True)
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
            response = False
            data = serializer.validated_data
            instance = data["camunda_process_id"]

            try:
                case = Case.objects.get(id=pk)
            except Case.DoesNotExist:
                return Response(
                    data="Camunda process has not started. Case does not exist",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if instance.to_directing_proccess:
                response = CamundaService().send_message_to_process_instance(
                    message_name=instance.camunda_message_name,
                    process_instance_id=case.directing_process,
                )
            else:
                case_process_instance = CaseProcessInstance.objects.create(case=case)
                case_process_id = case_process_instance.process_id.__str__()

                response = CamundaService().send_message(
                    message_name=instance.camunda_message_name,
                    case_identification=case.id,
                    case_process_id=case_process_id,
                )

                try:
                    json_response = response.json()[0]
                    camunda_process_id = json_response["processInstance"]["id"]
                except Exception:
                    return Response(
                        data=f"Camunda process has not started. Json response not valid {str(response.content)}",
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                case_process_instance.camunda_process_id = camunda_process_id
                case_process_instance.save()

            if response:
                return Response(
                    data=f"Process has started {str(response.content)}",
                    status=status.HTTP_200_OK,
                )

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
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data.update(
                {
                    "author": request.user,
                }
            )
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
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
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
            bag_result = do_bag_search_address_exact(d)
            d_clone = dict(d)
            if bag_result and bag_result["count"] == 1:
                d_clone["address"] = {
                    "bag_id": bag_result["results"][0]["adresseerbaar_object_id"]
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

    def _add_reason(self, data):
        reason, _ = CaseReason.objects.get_or_create(name=settings.DEFAULT_REASON)
        for d in data:
            d["reason"] = reason.id
        return data

    def _get_object(self, case_id):
        return Case.objects.filter(
            legacy_bwv_case_id=case_id, is_legacy_bwv=True
        ).first()

    def _create_or_update(self, data, request, commit):
        errors = []
        results = []
        context = {"request": request}
        for d in data:
            d_clone = dict(d)
            instance = self._get_object(d.get("legacy_bwv_case_id"))
            if instance:
                serializer = LegacyCaseUpdateSerializer(
                    instance, data=d, context=context
                )
            else:
                serializer = LegacyCaseCreateSerializer(data=d, context=context)

            if serializer.is_valid(raise_exception=True):
                d_clone.update(
                    {
                        "case": d.get("legacy_bwv_case_id"),
                        "created": False if instance else True,
                    }
                )
                if commit:
                    serializer.save()

                results.append(d_clone)
            else:
                errors.append(
                    {
                        "legacy_bwv_case_id": d.get("legacy_bwv_case_id"),
                        "errors": serializer.errors,
                    }
                )
        return errors, results

    def _parse_case_data_to_case_serializer(self, data):
        map = {
            "date_created_zaak": "start_date",
            "situatie_schets": "description",
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

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        create_update_results = []
        if request.GET.get("commit"):
            data = self.request.session.get("validated_cases_data")
            if data:
                create_update_errors, create_update_results = self._create_or_update(
                    data,
                    request,
                    True,
                )
                del self.request.session["validated_cases_data"]
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
        ) = address_mismatches = create_update_errors = create_update_results = []
        form_valid = False

        if form.is_valid():
            original_data = form.cleaned_data["json_data"]

            data = self._parse_case_data_to_case_serializer(original_data)
            data, address_mismatches = self._add_address(data)
            data = self._add_theme(data, *args, **kwargs)
            data = self._add_reason(data)
            create_update_errors, create_update_results = self._create_or_update(
                data,
                request,
                False,
            )
            form_valid = True
            self.request.session["validated_cases_data"] = create_update_results

        context.update(
            {
                "validation_form_valid": form_valid,
                "data": data,
                "original_data": original_data,
                "address_mismatches": address_mismatches,
                "create_update_errors": create_update_errors,
                "create_update_results": create_update_results,
            }
        )
        return self.render_to_response(context)


class CaseCloseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CaseCloseSerializer
    queryset = CaseClose.objects.all()
