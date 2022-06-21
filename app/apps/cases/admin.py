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
)
from apps.workflow.tasks import task_create_main_worflow_for_case
from django import forms
from django.contrib import admin


class LabelThemeModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.theme.name}: {obj.name}"


class CaseAdminForm(forms.ModelForm):
    class Meta:
        model = Case
        exclude = ()

    reason = LabelThemeModelChoiceField(
        queryset=CaseReason.objects.all(),
        required=False,
    )
    project = LabelThemeModelChoiceField(
        queryset=CaseProject.objects.all(),
        required=False,
    )


@admin.action(description="Create main workflow for case")
def create_main_worflow_for_case(modeladmin, request, queryset):
    for case in queryset.filter(is_legacy_camunda=True, end_date__isnull=True):
        task_create_main_worflow_for_case.delay(case.id)


@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "document_url",
        "connected",
    )
    search_fields = ("case__id",)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    form = CaseAdminForm
    list_display = (
        "id",
        "theme",
        "reason",
        "project",
        "identification",
        "start_date",
        "end_date",
        "address",
        "legacy_bwv_case_id",
        "is_legacy_bwv",
        "case_url",
        "author",
    )
    list_filter = (
        "theme",
        "reason",
        "is_legacy_bwv",
        "is_legacy_camunda",
        "project",
        "subjects",
        "address__housing_corporation",
    )
    search_fields = ("id", "legacy_bwv_case_id")
    actions = [
        create_main_worflow_for_case,
    ]


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
        "set_in_open_zaak",
    )
    list_filter = ("status",)
    search_fields = ("case__id",)


@admin.register(CaseStateType)
class CaseStateTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )


@admin.register(CitizenReport)
class CitizenReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "identification",
        "reporter_name",
        "reporter_phone",
        "reporter_email",
        "description_citizenreport",
        "nuisance",
        "author",
        "date_added",
        "case_user_task_id",
    )
    search_fields = ("case__id",)


@admin.register(CaseReason)
class CaseReasonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
    )
    list_filter = ("theme",)


@admin.register(CaseProject)
class CaseProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
        "active",
    )
    list_filter = ("theme",)
    list_editable = ("active",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
    )
    list_filter = (
        "theme",
        "name",
    )


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
