from apps.events.models import CaseEvent
from django.contrib import admin

admin.site.register(
    CaseEvent,
    admin.ModelAdmin,
    readonly_fields=("date_created", "event_values"),
    list_display=("id", "emitter"),
)
