from django.conf.urls import url
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html, mark_safe

from .forms import ResetSubworkflowsForm, UpdateDataForWorkflowsForm
from .models import CaseUserTask, CaseWorkflow, GenericCompletedTask, WorkflowOption
from .tasks import task_update_workflow


@admin.action(description="Force update workflows")
def force_update_workflows(modeladmin, request, queryset):
    for workflow in queryset.all():
        task_update_workflow.delay(workflow.id)


@admin.action(description="Migrate to latest")
def migrate_worflows_to_latest(modeladmin, request, queryset):
    results = []
    test = request.POST.get("confirmation") is None
    for caseworkflow in queryset.all():
        result, success = caseworkflow.migrate_to_latest(test)
        results.append(
            {
                "workflow_id": caseworkflow.id,
                "result": result,
                "success": success,
            }
        )
    if request.POST.get("confirmation") is None:
        request.current_app = modeladmin.admin_site.name

        incompatible_migrations = sorted(
            [r for r in results if not r.get("success")],
            key=lambda d: str(d.get("result", {}).get("workflow_result")),
        )
        compatible_migrations = [r for r in results if r.get("success")]

        context = {
            "action": request.POST["action"],
            "queryset": queryset,
            "incompatible_migrations": incompatible_migrations,
            "compatible_migrations": compatible_migrations,
        }
        return TemplateResponse(
            request, "admin/workflow/caseworkflow/migrate_to_latest.html", context
        )


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
        "update_data",
        "reset_subworkflows",
    )

    list_filter = (
        "main_workflow",
        "workflow_type",
        "workflow_version",
        "workflow_theme_name",
    )
    search_fields = ("case__id",)

    actions = (
        migrate_worflows_to_latest,
        force_update_workflows,
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
            (
                migrate_to_latest_result,
                migrate_to_latest_success,
            ) = obj.migrate_to_latest()
            context.update(
                {
                    "migrate_to_latest_success": migrate_to_latest_success,
                    "migrate_to_latest_result": migrate_to_latest_result,
                    "workflow": obj.get_or_restore_workflow_state(),
                    "task_states": ["COMPLETED", "READY", "WAITING", "CANCELLED"],
                }
            )
            obj.reset_subworkflow("debrief")
        return super().render_change_form(request, context, add, change, form_url, obj)

    def reset_subworkflows(self, obj):
        if obj.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DIRECTOR:
            return format_html(
                '<a class="button" href="{}" id="caseworkflow_id_{}">Reset&nbsp;subworkflows</a>',
                reverse("admin:reset-subworkflows", args=[obj.pk]),
                obj.pk,
            )
        else:
            return ""

    reset_subworkflows.short_description = "Reset subworkflows"
    reset_subworkflows.allow_tags = True

    def update_data(self, obj):
        return format_html(
            '<a class="button" href="{}" id="caseworkflow_id_{}">Update&nbsp;data</a>',
            reverse("admin:update-data-for-subworkflow", args=[obj.pk]),
            obj.pk,
        )

    update_data.short_description = "Update data"
    update_data.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r"^(?P<caseworkflow_id>.+)/reset-subworkflows/$",
                self.admin_site.admin_view(self.admin_process_reset_subworkflows),
                name="reset-subworkflows",
            ),
            url(
                r"^(?P<caseworkflow_id>.+)/update-data-for-subworkflow/$",
                self.admin_site.admin_view(self.admin_update_data_for_workflow),
                name="update-data-for-subworkflow",
            ),
        ]
        return custom_urls + urls

    def admin_process_reset_subworkflows(
        self, request, caseworkflow_id, *args, **kwargs
    ):
        caseworkflow = self.get_object(request, caseworkflow_id)
        result = {}
        if request.method == "GET":
            form = ResetSubworkflowsForm(caseworkflow=caseworkflow)
            if request.GET.get("reset_to"):
                result = caseworkflow.reset_subworkflow(
                    request.GET.get("reset_to"), False
                )
                messages.add_message(
                    request,
                    messages.INFO,
                    f"De workflow director '{caseworkflow.id}' is gemigreert naar de laatste versie en gereset naar de de subworkflow '{request.GET.get('reset_to')}'",
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

    def admin_update_data_for_workflow(self, request, caseworkflow_id, *args, **kwargs):
        caseworkflow = self.get_object(request, caseworkflow_id)
        result = {}
        success = False
        form = UpdateDataForWorkflowsForm(caseworkflow=caseworkflow)
        if request.method == "POST":
            form = UpdateDataForWorkflowsForm(request.POST, caseworkflow=caseworkflow)
            if form.is_valid():
                result, success = form.save(
                    caseworkflow, not request.POST.get("update", False)
                )
            if request.POST.get("update", False):
                messages.add_message(
                    request,
                    messages.INFO,
                    f"De data voor de workflow '{caseworkflow.id}' is aangepast",
                )
                url = reverse(
                    "admin:update-data-for-subworkflow",
                    args=[caseworkflow.pk],
                    current_app=self.admin_site.name,
                )
                return HttpResponseRedirect(f"{url}")

        context = self.admin_site.each_context(request)
        context.update(
            {
                "opts": self.model._meta,
                "form": form,
                "caseworkflow": caseworkflow,
                "success": success,
                "result": result,
                "workflow": caseworkflow.get_or_restore_workflow_state(),
                "task_states": ["COMPLETED", "READY", "WAITING", "CANCELLED"],
                "title": "Update data for workflow",
            }
        )
        return TemplateResponse(
            request,
            "admin/workflow/caseworkflow/update_data_for_workflow.html",
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
