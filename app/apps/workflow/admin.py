from django.contrib import admin

from .models import CaseUserTask, CaseWorkflow


@admin.register(CaseWorkflow)
class CaseWorkflowAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "main_workflow",
        "workflow_type",
        "workflow_version",
        "workflow_theme_name",
    )

    list_filter = (
        "main_workflow",
        "workflow_type",
        "workflow_version",
        "workflow_theme_name",
    )

    def chart_data(self):
        return "test data"

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        if obj:
            obj.migrate_to("0.2.0")
            context.update(
                {
                    "workflow": obj.get_or_restore_workflow_state(),
                    "task_states": ["COMPLETED", "READY", "WAITING", "CANCELLED"],
                }
            )
        return super().render_change_form(request, context, add, change, form_url, obj)


@admin.register(CaseUserTask)
class CaseTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "task_id",
        "name",
        "task_name",
        "completed",
        "workflow",
    )
