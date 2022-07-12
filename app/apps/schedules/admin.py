from apps.schedules.models import Action, DaySegment, Priority, Schedule, WeekSegment
from apps.workflow.utils import complete_uncompleted_task_for_event_emitters
from django.contrib import admin


@admin.action(description="Complete task for this schedule")
def complete_task_for_event_emitter(modeladmin, request, queryset):
    for instance in queryset.exclude(case_user_task_id="-1"):
        complete_uncompleted_task_for_event_emitters(instance)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "date_added",
        "case_user_task_id",
        "action",
        "week_segment",
        "day_segment",
        "priority",
        "visit_from_datetime",
    )
    search_fields = ("case__id",)

    list_filter = (
        "action",
        "week_segment",
        "day_segment",
        "priority",
    )
    actions = (complete_task_for_event_emitter,)


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
    )
    list_filter = ("theme",)


@admin.register(DaySegment)
class DaySegmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
    )
    list_filter = ("theme",)


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "weight",
        "theme",
    )
    list_filter = ("theme",)


@admin.register(WeekSegment)
class WeekSegmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "theme",
    )
    list_filter = ("theme",)
