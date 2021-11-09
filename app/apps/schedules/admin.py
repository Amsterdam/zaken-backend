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


admin.site.register(DaySegment, admin.ModelAdmin)
admin.site.register(Priority, admin.ModelAdmin)
admin.site.register(Action, admin.ModelAdmin)
admin.site.register(WeekSegment, admin.ModelAdmin)
