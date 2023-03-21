from apps.summons.models import Summon, SummonedPerson, SummonType
from django.contrib import admin

admin.site.register(
    SummonType,
    admin.ModelAdmin,
    list_display=("id", "name", "workflow_option", "theme"),
    list_filter=(
        "theme",
        "workflow_option",
    ),
    search_fields=("name",),
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
    list_filter = (
        "date_added",
        "case__theme",
        "type",
    )
    search_fields = ("case__id",)
    list_editable = ("type",)


admin.site.register(
    SummonedPerson,
    admin.ModelAdmin,
    list_display=(
        "first_name",
        "preposition",
        "last_name",
        "entity_name",
        "function",
        "person_role",
        "summon",
    ),
    list_filter=("person_role",),
    search_fields=(
        "last_name",
        "entity_name",
    ),
)
