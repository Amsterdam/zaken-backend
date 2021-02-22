from apps.cases.models import Case, CaseReason, CaseState, CaseStateType, CaseTeam
from django.contrib import admin


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("id", "identification", "start_date", "end_date", "address")


@admin.register(CaseState)
class CaseStateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "start_date",
        "end_date",
    )


admin.site.register(CaseStateType, admin.ModelAdmin)
admin.site.register(CaseTeam, admin.ModelAdmin)
admin.site.register(CaseReason, admin.ModelAdmin)
