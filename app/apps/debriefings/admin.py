from apps.debriefings.models import Debriefing
from django.contrib import admin

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
