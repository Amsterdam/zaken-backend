import datetime
import logging
import mimetypes
import os
from collections import OrderedDict

import requests
from apps.addresses.models import HousingCorporation
from apps.cases.forms import ImportBWVCaseDataForm
from apps.cases.models import Case, CaseProject, CaseReason, CaseTheme
from apps.cases.serializers import (
    BWVMeldingenSerializer,
    BWVStatusSerializer,
    LegacyCaseCreateSerializer,
)
from apps.users.models import User
from apps.visits.models import Visit
from apps.visits.serializers import VisitSerializer
from apps.workflow.models import GenericCompletedTask
from apps.workflow.serializers import GenericCompletedTaskCreateSerializer
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.edit import FormView
from utils.api_queries_bag import do_bag_search_address_exact

logger = logging.getLogger(__name__)


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
        "melding": "SIA melding",
        "sia_melding": "SIA melding",
        "sia": "SIA melding",
        "project": "Project",
        "digitaal_toezicht": "Digitaal toezicht",
        "melding_eigenaar": "Leegstandsmelding eigenaar",
        "melding_bi": "BI melding",
        "eigen_onderzoek": "Eigen onderzoek",
        "corporatie_melding": "Corporatie melding",
        "politie_(SBA2.0)": "Politie (SBA 2.0)",
        "doorzon": "Doorzon",
        "ilprowo": "Ilprowo",
        "mma": "MMA",
        "leegstandsmelding_eigenaar": "Leegstandsmelding eigenaar",
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
        "WS_TOELICHTING": "Toelichting",
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
                d_clone["bag_id"] = bag_result[0]["adresseerbaar_object_id"]
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

    def add_housing_corporation(self, data, *args, **kwargs):
        for d in data:
            existing_corpo = (
                d.get("housing_corporation")
                if d.get("housing_corporation") is not None
                else "thisisnocorporation"
            )
            housing_corporation = HousingCorporation.objects.filter(
                bwv_name__icontains=existing_corpo
            ).first()
            d["housing_corporation"] = (
                housing_corporation.id if housing_corporation else None
            )
        return data

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

            d["subworkflow"] = kwargs.get("subworkflow")
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
                    date_added=datetime.datetime.strptime(
                        e["date_added"], "%d-%m-%Y %H:%M:%S %z"
                    ),
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
            events_serializer = GenericCompletedTaskCreateSerializer(
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
                logger.info(
                    f"GenericCompletedTaskCreateSerializer errors: case '{case}'"
                )
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
            "ADS_WOCO": "housing_corporation",
        }

        def to_int(v):

            try:
                v = int(v.strip().split(".")[0])
            except Exception:
                pass
            return v

        transform = {
            "huisnummer": to_int,
            "toev": to_int,
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
                        key=lambda d: d.get("HM_DATE_CREATED"),
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
                        date_added = (
                            f'{status_variables.get("HM_DATE_CREATED")} 00:00:00 +0000'
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
                                "date_added": date_added,
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
                        date_added = (
                            f'{status_variables.get("WS_DATE_CREATED")} 00:00:00 +0000'
                        )
                        status_data = {
                            "description": f"BWV Status: {status_variables.get('WS_STA_CD_OMSCHRIJVING')}",
                            "variables": {
                                "mapped_form_data": mapped_form_data,
                                "bwv_id": status_variables.get("STADIUM_ID"),
                            },
                            "date_added": date_added,
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
        data = self.add_housing_corporation(data, *args, **kwargs)
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
                    "subworkflow",
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
