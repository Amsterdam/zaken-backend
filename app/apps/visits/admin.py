from django.contrib import admin

from .models import Visit


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "completed",
        "situation",
        "can_next_visit_go_ahead",
        "case_user_task_id",
        "start_time",
    )
    search_fields = ("case__id",)
