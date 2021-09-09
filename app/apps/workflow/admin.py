from django.contrib import admin

from .models import Task, Workflow


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "task_id",
        "name",
        "task_name_id",
        "completed",
        "workflow",
    )


admin.site.register(Workflow, admin.ModelAdmin)
