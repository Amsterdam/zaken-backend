from apps.schedules.models import Action, DaySegment, Priority, Schedule, WeekSegment
from django.contrib import admin

admin.site.register(DaySegment, admin.ModelAdmin)
admin.site.register(Priority, admin.ModelAdmin)
admin.site.register(Schedule, admin.ModelAdmin)
admin.site.register(Action, admin.ModelAdmin)
admin.site.register(WeekSegment, admin.ModelAdmin)
