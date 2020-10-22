from apps.debriefings.models import Debriefing
from django.contrib import admin

admin.site.register(
    Debriefing,
    admin.ModelAdmin,
    list_display=(
        "case",
        "date_added",
        "date_modified",
        "author",
        "violation",
    ),
)
