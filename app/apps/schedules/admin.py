from apps.schedules.models import Action, DaySegment, Priority, Schedule, WeekSegment
from django.contrib import admin


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "date_added",
        "case_user_task_id",
    )
    search_fields = ("case__id",)


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
