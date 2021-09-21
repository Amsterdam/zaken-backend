from django.contrib import admin

from .models import Task, Workflow


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "main_workflow",
        "workflow_type",
        "workflow_version",
    )

    def chart_data(self):
        return "test data"

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        if obj:
            context.update(
                {
                    "first_task": obj.first_task(),
                    "task_states": ["COMPLETED", "READY", "WAITING", "CANCELLED"],
                }
            )
        return super().render_change_form(request, context, add, change, form_url, obj)


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
