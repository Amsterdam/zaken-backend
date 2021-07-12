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
from django.contrib import admin


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
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
