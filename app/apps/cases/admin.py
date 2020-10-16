from apps.cases.models import (
    Address,
    Case,
    CaseState,
    CaseStateType,
    CaseTimelineReaction,
    CaseTimelineSubject,
    CaseTimelineThread,
    CaseType,
    OpenZaakState,
    OpenZaakStateType,
)
from django.contrib import admin


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("identification", "start_date", "end_date", "case_type", "address")


@admin.register(CaseType)
class CaseTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


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


@admin.register(OpenZaakStateType)
class OpenZaakStateTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(OpenZaakState)
class OpenZaakStateAdmin(admin.ModelAdmin):
    list_display = ("__str__",)


admin.site.register(CaseState, admin.ModelAdmin)
admin.site.register(CaseStateType, admin.ModelAdmin)
admin.site.register(CaseTimelineSubject, admin.ModelAdmin)
admin.site.register(CaseTimelineThread, admin.ModelAdmin)
admin.site.register(CaseTimelineReaction, admin.ModelAdmin)
