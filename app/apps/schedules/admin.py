from apps.schedules.models import (
    DaySegment,
    Priority,
    Schedule,
    ScheduleType,
    WeekSegment,
)
from django.contrib import admin

admin.site.register(DaySegment, admin.ModelAdmin)
admin.site.register(Priority, admin.ModelAdmin)
admin.site.register(Schedule, admin.ModelAdmin)
admin.site.register(ScheduleType, admin.ModelAdmin)
admin.site.register(WeekSegment, admin.ModelAdmin)
