from apps.events.models import CaseEvent
from django.contrib import admin

admin.site.register(
    CaseEvent,
    admin.ModelAdmin,
    readonly_fields=("date_created", "event_values"),
    list_display=(
        "id",
        "emitter",
        "emitter_id",
        "emitter_type",
        "type",
        "date_created",
    ),
    list_filter=(
        "date_created",
        "type",
    ),
    search_fields=("emitter_id",),
    ordering=("-id",),
)
