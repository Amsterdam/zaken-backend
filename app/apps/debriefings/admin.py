from apps.debriefings.models import Debriefing
from django.contrib import admin

from .models import ViolationType

admin.site.register(
    Debriefing,
    admin.ModelAdmin,
    list_display=(
        "id",
        "case",
        "date_added",
        "date_modified",
        "author",
        "violation",
        "case_user_task_id",
    ),
    search_fields=("case__id",),
    list_filter=("date_added",),
)


@admin.register(ViolationType)
class ViolationTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "value",
        "theme",
        "enabled",
    )
    list_filter = ("theme", "enabled")
