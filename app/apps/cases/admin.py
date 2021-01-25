from apps.cases.models import Case, CaseReason, CaseState, CaseStateType, CaseTeam
from django.contrib import admin


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("id", "identification", "start_date", "end_date", "address")


admin.site.register(CaseState, admin.ModelAdmin)
admin.site.register(CaseStateType, admin.ModelAdmin)
admin.site.register(CaseTeam, admin.ModelAdmin)
admin.site.register(CaseReason, admin.ModelAdmin)
