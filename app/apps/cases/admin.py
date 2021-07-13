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
from django import forms
from django.contrib import admin


def get_project_choises():
    return [
        (item, f"{item.theme.name}: {item.name}") for item in CaseProject.objects.all()
    ]


def get_reason_choises():
    return [
        (reason, f"{reason.case_theme.name}: {reason.name}")
        for reason in CaseCloseReason.objects.all()
    ]


class CaseAdminForm(forms.ModelForm):
    class Meta:
        model = Case
        exclude = ()

    reason = forms.ChoiceField(choices=get_reason_choises)
    project = forms.ChoiceField(choices=get_project_choises)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    form = CaseAdminForm
    list_display = (
        "id",
        "identification",
        "start_date",
        "end_date",
        "address",
        "legacy_bwv_case_id",
        "is_legacy_bwv",
    )


@admin.register(CaseState)
class CaseStateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "start_date",
        "end_date",
    )


@admin.register(CitizenReport)
class CitizenReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "identification",
        "reporter_name",
        "reporter_phone",
    )


@admin.register(CaseReason)
class CaseReasonAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "theme",
    )
    list_filter = ("theme",)


@admin.register(CaseProject)
class CaseProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "theme",
    )
    list_filter = ("theme",)


@admin.register(CaseCloseReason)
class CaseCloseReasonAdmin(admin.ModelAdmin):
    list_display = (
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
        "name",
        "case_theme",
    )
    list_filter = ("case_theme",)


@admin.register(CaseProcessInstance)
class CaseProcessInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "process_id",
        "case",
        "camunda_process_id",
    )
    search_fields = (
        "process_id",
        "camunda_process_id",
    )


admin.site.register(CaseStateType, admin.ModelAdmin)
admin.site.register(CaseTheme, admin.ModelAdmin)
admin.site.register(CaseClose, admin.ModelAdmin)
