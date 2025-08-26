from datetime import date, timedelta

from apps.cases.models import (
    Advertisement,
    Case,
    CaseClose,
    CaseCloseReason,
    CaseCloseResult,
    CaseDocument,
    CaseProject,
    CaseReason,
    CaseState,
    CaseStateType,
    CaseTheme,
    CitizenReport,
    Subject,
    Tag,
)
from apps.workflow.tasks import task_create_main_worflow_for_case
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from openpyxl import Workbook


class LabelThemeModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.theme.name}: {obj.name}"


class CaseAdminForm(forms.ModelForm):
    class Meta:
        model = Case
        exclude = ()

    reason = LabelThemeModelChoiceField(
        queryset=CaseReason.objects.all(),
        required=True,
    )
    project = LabelThemeModelChoiceField(
        queryset=CaseProject.objects.all(),
        required=False,
    )


@admin.action(description="Create main workflow for case")
def create_main_worflow_for_case(modeladmin, request, queryset):
    for case in queryset.filter(is_legacy_camunda=True, end_date__isnull=True):
        task_create_main_worflow_for_case.delay(case.id)


@admin.action(
    description="Migrate advertisement_linklist items to Advertisement instance"
)
def migrate_advertisement_linklist_items(modeladmin, request, queryset):
    queryset = queryset.filter(advertisement_linklist__len__gt=0).order_by(
        "-date_added"
    )
    for citizen_report in queryset:
        for link in citizen_report.advertisement_linklist:
            if (
                citizen_report.case.reason.name == "SIG melding"
                and date(
                    year=citizen_report.date_added.year,
                    month=citizen_report.date_added.month,
                    day=citizen_report.date_added.day,
                )
                == citizen_report.case.start_date
            ):
                related_object = citizen_report.case
            else:
                related_object = citizen_report
            related_object_type = ContentType.objects.get_for_model(related_object)
            if Advertisement.objects.filter(
                case=citizen_report.case,
                link=link,
                related_object_id=related_object.id,
                related_object_type=related_object_type,
                date_added=citizen_report.date_added,
            ):
                continue
            advertisement_instance = Advertisement(
                case=citizen_report.case,
                link=link,
                related_object=related_object,
            )
            advertisement_instance.save()
            advertisement_instance.date_added = citizen_report.date_added
            advertisement_instance.save()


@admin.action(description="Remove advertisement_linklist items")
def remove_advertisement_linklist_items(modeladmin, request, queryset):
    queryset = queryset.filter(advertisement_linklist__len__gt=0).order_by(
        "-date_added"
    )
    for citizen_report in queryset:
        citizen_report.advertisement_linklist = []
        citizen_report.save()


def export_queryset_to_excel(modeladmin, request, queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Zaken"
    headers = ["Zaak ID", "Address", "Thema", "Aanleiding", "Startdatum", "Einddatum"]
    ws.append(headers)

    for case in queryset:
        # Format the dates in 'DD-MM-YYYY' format
        start_date_formatted = (
            case.start_date.strftime("%d-%m-%Y") if case.start_date else ""
        )
        end_date_formatted = case.end_date.strftime("%d-%m-%Y") if case.end_date else ""

        ws.append(
            [
                case.id,
                case.address.full_address,
                case.theme.name,
                case.reason.name,
                start_date_formatted,
                end_date_formatted,
            ]
        )

    # Create an HTTP response with the Excel file
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=aza_cases_export.xlsx"

    wb.save(response)
    return response


# Short description for the action, which will be displayed in the admin action dropdown
export_queryset_to_excel.short_description = "Export Cases to Excel"


@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "document_url",
        "connected",
    )
    search_fields = ("case__id",)


class BewaartermijnFilter(admin.SimpleListFilter):
    title = _("Verlopen Bewaartermijnen")
    parameter_name = "bewaartermijn"

    def lookups(self, request, model_admin):
        """Options that will appear in the filter dropdown."""
        return (
            ("toezicht_5_jaar", _("Toezicht bewaartermijn (5 jaar)")),
            ("handhaving_10_jaar", _("Handhaving bewaartermijn (10 jaar)")),
        )

    def queryset(self, request, queryset):
        """Filter the queryset based on the selected filter option."""
        if self.value() == "toezicht_5_jaar":
            # Filter cases that ended more than 5 years ago and have NO status HANDHAVING
            five_years_ago = timezone.now().date() - timedelta(days=5 * 365)
            return queryset.exclude(
                Exists(
                    CaseState.objects.filter(
                        case=OuterRef("pk"), status=CaseState.CaseStateChoice.HANDHAVING
                    )
                )
            ).filter(end_date__lt=five_years_ago)
        elif self.value() == "handhaving_10_jaar":
            # Filter cases that ended more than 10 years ago and have a status HANDHAVING
            ten_years_ago = timezone.now().date() - timedelta(days=10 * 365)
            return queryset.filter(
                Exists(
                    CaseState.objects.filter(
                        case=OuterRef("pk"), status=CaseState.CaseStateChoice.HANDHAVING
                    )
                ),
                end_date__lt=ten_years_ago,
            )
        return queryset


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    form = CaseAdminForm
    list_display = (
        "id",
        "address",
        "theme",
        "start_date",
        "end_date",
        "is_legacy_bwv",
    )
    list_filter = (
        "theme",
        BewaartermijnFilter,
        "start_date",
        "end_date",
        "address__housing_corporation",
        "is_legacy_bwv",
        "is_legacy_camunda",
        "reason",
        "project",
        "subjects",
        "tags",
    )
    search_fields = (
        "id",
        "legacy_bwv_case_id",
        "address__street_name",
        "address__postal_code",
    )
    actions = [create_main_worflow_for_case, export_queryset_to_excel]


@admin.register(CaseTheme)
class CaseThemeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "sensitive",
    )


@admin.register(CaseState)
class CaseStateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "status",
        "created",
        "last_updated",
        "set_in_open_zaak",
    )
    list_filter = (
        "status",
        "set_in_open_zaak",
        "created",
        "last_updated",
    )
    search_fields = ("case__id",)


@admin.register(CaseStateType)
class CaseStateTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )
    search_fields = ("name",)


@admin.register(CitizenReport)
class CitizenReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "identification",
        "reporter_name",
        "reporter_phone",
        "reporter_email",
        "description_citizenreport",
        "nuisance",
        "author",
        "date_added",
        "case_user_task_id",
        "advertisement_linklist",
    )
    search_fields = ("case__id",)
    actions = (
        migrate_advertisement_linklist_items,
        remove_advertisement_linklist_items,
    )


@admin.register(CaseReason)
class CaseReasonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
    )
    list_filter = ("theme",)
    search_fields = ("name",)


@admin.register(CaseProject)
class CaseProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
        "active",
    )
    list_filter = (
        "theme",
        "active",
    )
    list_editable = ("active",)
    search_fields = ("name",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
    )
    list_filter = ("theme",)
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
    )
    list_filter = ("theme",)
    search_fields = ("name",)


@admin.register(CaseCloseReason)
class CaseCloseReasonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "case_theme",
        "result",
    )
    list_filter = (
        "case_theme",
        "result",
    )


@admin.register(CaseCloseResult)
class CaseCloseResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "case_theme",
    )
    list_filter = ("case_theme",)


@admin.register(CaseClose)
class CaseCloseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "reason",
        "date_added",
        "case_user_task_id",
    )
    search_fields = ("case__id",)
    list_editable = ("reason",)
    list_filter = ("reason",)


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "link",
        "related_object",
    )
    search_fields = ("case__id",)
