from apps.summons.models import Summon, SummonedPerson, SummonType
from django.contrib import admin

admin.site.register(
    SummonType,
    admin.ModelAdmin,
    list_display=("id", "name", "workflow_option", "theme"),
    list_filter=(
        "workflow_option",
        "theme",
    ),
)


@admin.register(Summon)
class SummonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "type",
        "date_added",
        "case_user_task_id",
    )
    search_fields = ("case__id",)


admin.site.register(SummonedPerson, admin.ModelAdmin)
