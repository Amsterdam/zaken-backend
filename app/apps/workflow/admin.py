from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html, mark_safe

from .forms import ResetSubworkflowsForm
from .models import CaseUserTask, CaseWorkflow, GenericCompletedTask, WorkflowOption


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
        "completed",
        "reset_subworkflows",
    )

    list_filter = (
        "main_workflow",
        "workflow_type",
        "workflow_version",
        "workflow_theme_name",
    )
    search_fields = ("case__id",)

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
            obj.reset_subworkflow("debrief")
        return super().render_change_form(request, context, add, change, form_url, obj)

    def reset_subworkflows(self, obj):
        if obj.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DIRECTOR:
            return format_html(
                '<a class="button" href="{}" id="caseworkflow_id_{}">Reset subworkflows</a>',
                reverse("admin:reset-subworkflows", args=[obj.pk]),
                obj.pk,
            )
        else:
            return ""

    reset_subworkflows.short_description = "Reset subworkflows"
    reset_subworkflows.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r"^(?P<caseworkflow_id>.+)/reset-subworkflows/$",
                self.admin_site.admin_view(self.process_reset_subworkflows),
                name="reset-subworkflows",
            ),
        ]
        return custom_urls + urls

    def process_reset_subworkflows(self, request, caseworkflow_id, *args, **kwargs):
        caseworkflow = self.get_object(request, caseworkflow_id)
        result = {}
        if request.method == "GET":
            form = ResetSubworkflowsForm(caseworkflow=caseworkflow)
            if request.GET.get("reset_to"):
                result = caseworkflow.reset_subworkflow(
                    request.GET.get("reset_to"), False
                )
                url = reverse(
                    "admin:reset-subworkflows",
                    args=[caseworkflow.pk],
                    current_app=self.admin_site.name,
                )
                return HttpResponseRedirect(f"{url}?done=true")
        else:
            form = ResetSubworkflowsForm(request.POST, caseworkflow=caseworkflow)
            if form.is_valid():
                result = form.save(caseworkflow)

        context = self.admin_site.each_context(request)

        context.update(
            {
                "opts": self.model._meta,
                "form": form,
                "caseworkflow": caseworkflow,
                "result": result,
                "workflow": caseworkflow.get_or_restore_workflow_state(),
                "task_states": ["COMPLETED", "READY", "WAITING", "CANCELLED"],
                "title": "Reset subworkflows for director",
            }
        )
        return TemplateResponse(
            request,
            "admin/workflow/caseworkflow/reset_subworkflows.html",
            context,
        )


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
    search_fields = ("case__id",)
    list_filter = ("task_name", "name")


@admin.register(WorkflowOption)
class WorkflowOptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "message_name",
        "to_directing_proccess",
        "theme",
    )


@admin.register(GenericCompletedTask)
class GenericCompletedTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case",
        "date_added",
        "description",
        "author",
        "case_user_task_id",
    )
    search_fields = ("case__id",)
    list_filter = ("description",)
