from apps.cases.models import (
    Address,
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


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "bag_id",
        "postal_code",
        "street_name",
        "number",
        "suffix_letter",
        "suffix",
    )


admin.site.register(CaseState, admin.ModelAdmin)
admin.site.register(CaseStateType, admin.ModelAdmin)
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
