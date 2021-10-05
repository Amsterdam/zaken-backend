from django.contrib import admin
from django.utils.html import mark_safe

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
        "parent_workflow",
        "issues",
    )

    list_filter = (
        "main_workflow",
        "workflow_type",
        "workflow_version",
        "workflow_theme_name",
    )

    def issues(self, obj):
        issues = obj.check_for_issues()
        if issues == "no issues":
            return f"{issues}"
        return mark_safe(f"<span style='color: red;'>{issues}</span>")

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        if obj:
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
