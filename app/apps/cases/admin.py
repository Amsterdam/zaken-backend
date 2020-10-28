from apps.cases.models import (
    Case,
    CaseState,
    CaseStateType,
    CaseTimelineReaction,
    CaseTimelineSubject,
    CaseTimelineThread,
)
from django.contrib import admin


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("identification", "start_date", "end_date", "address")


admin.site.register(
    CaseTimelineSubject, admin.ModelAdmin, list_display=("case", "subject", "is_done")
)
admin.site.register(
    CaseTimelineThread,
    admin.ModelAdmin,
    list_display=(
        "date",
        "subject",
    ),
)
admin.site.register(CaseTimelineReaction, admin.ModelAdmin)
