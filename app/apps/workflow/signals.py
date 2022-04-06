import copy
import datetime

import pytz
from apps.events.models import TaskModelEventEmitter
from apps.workflow.models import CaseUserTask, CaseWorkflow, GenericCompletedTask
from apps.workflow.tasks import task_start_worflow
from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow

from .user_tasks import DEFAULT_USER_TASK_DUE_DATE, get_task_by_name
from .utils import get_latest_version_from_config


@receiver(pre_save, dispatch_uid="event_emitter_pre_save")
def event_emitter_pre_save(instance, **kwargs):
    if kwargs.get("raw"):
        return
    if (
        issubclass(instance.__class__, TaskModelEventEmitter)
        and not instance.id
        and hasattr(instance, "case_user_task_id")
        and instance.case_user_task_id
        and instance.case_user_task_id != "-1"
    ):
        type_instance = instance.__class__.objects.filter(
            case_user_task_id=instance.case_user_task_id
        )
        if type_instance:
            raise Exception(
                f"TaskModelEventEmitter of type '{instance.__class__.__name__}', with '{instance.case_user_task_id}', already exists"
            )


@receiver(pre_save, sender=CaseUserTask, dispatch_uid="case_user_task_pre_save")
def case_user_task_pre_save(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return
    if not instance.id:
        now = timezone.now()
        d = datetime.datetime(
            year=now.year, month=now.month, day=now.day, tzinfo=pytz.UTC
        )
        task = get_task_by_name(instance.task_name)
        task_elapse_datetime = instance.workflow.get_task_elapse_datetime(
            instance.task_id
        )
        cached_task_key = (
            f"parent_workflow_{instance.workflow.parent_workflow.id}_{instance.task_name}_due_date"
            if instance.workflow.parent_workflow
            else None
        )
        cached_task = cache.get(cached_task_key) if cached_task_key else None
        if cached_task:
            instance.due_date = cached_task.get("due_date")
            instance.owner = cached_task.get("owner")
            cache.delete(cached_task_key)
        elif isinstance(task_elapse_datetime, datetime.datetime):
            instance.due_date = task_elapse_datetime
        else:
            instance.due_date = d + (
                task.get_due_date(instance) if task else DEFAULT_USER_TASK_DUE_DATE
            )
    else:
        previous = CaseUserTask.objects.get(id=instance.id)
        if instance.due_date != previous.due_date:
            instance.workflow.set_task_elapse_datetime(
                instance.task_id, instance.due_date
            )


@receiver(post_save, sender=CaseUserTask, dispatch_uid="case_user_task_post_save")
def case_user_task_post_save(sender, instance, created, **kwargs):
    if created:
        user_task_type = get_task_by_name(instance.task_name)
        user_task_instance = user_task_type(instance)
        user_task_instance.instance_created()
        instance.case.force_citizen_report_feedback(instance)


@receiver(pre_save, sender=CaseWorkflow, dispatch_uid="case_workflow_pre_save")
def case_workflow_pre_save(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return
    if not instance.id:
        existing_main_workflows = CaseWorkflow.objects.filter(
            case=instance.case,
            main_workflow=True,
        ).first()
        if instance.main_workflow and existing_main_workflows:
            raise Exception("A main workflow for this case already exists")

        instance.data = instance.data if isinstance(instance.data, dict) else {}

        theme = instance.case.theme.snake_case_name
        reason = instance.case.reason.snake_case_name
        if instance.main_workflow:
            instance.data.update(
                {
                    "leegstandsmelding_eigenaar": {
                        "value": "ja"
                        if reason == "leegstandsmelding_eigenaar"
                        else "default",
                    },
                }
            )
            if reason == "handhavingsverzoek":
                CaseWorkflow.objects.create(
                    case=instance.case,
                    workflow_type="sub_workflow",
                    workflow_message_name="start_handhavingsverzoek",
                )
        if instance.workflow_type == CaseWorkflow.WORKFLOW_TYPE_DIRECTOR:
            instance.data.update(
                {
                    "theme": {"value": f"theme_{theme}"},
                    "reason": {"value": f"reason_{reason}"},
                }
            )

        current_verion = (
            existing_main_workflows.workflow_version
            if existing_main_workflows
            else None
        )
        if (
            instance.workflow_message_name == "start_handhavingsverzoek"
            and instance.workflow_type == "sub_workflow"
            and not instance.case.is_enforcement_request
        ):
            instance.case.is_enforcement_request = True
            instance.case.save()

        (
            instance.workflow_theme_name,
            instance.workflow_version,
        ) = get_latest_version_from_config(
            instance.case.theme.name,
            instance.workflow_type,
            current_verion,
        )
        workflow_spec = instance.get_workflow_spec()
        wf = BpmnWorkflow(workflow_spec)
        wf = instance.get_serializer().serialize_workflow(wf, include_spec=False)
        instance.serialized_workflow_state = wf


@receiver(post_save, sender=CaseWorkflow, dispatch_uid="start_workflow")
def start_workflow(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if created:
        task_start_worflow(instance.id)


@receiver(
    post_save,
    sender=GenericCompletedTask,
    dispatch_uid="complete_generic_user_task_and_create_new_user_tasks",
)
def complete_generic_user_task_and_create_new_user_tasks(
    sender, instance, created, **kwargs
):
    if kwargs.get("raw"):
        return
    task = CaseUserTask.objects.filter(id=instance.case_user_task_id).first()
    if created and task:
        data = copy.deepcopy(instance.variables)
        data.pop("mapped_form_data")
        user_task_type = get_task_by_name(task.task_name)
        user_task_instance = user_task_type(task)
        data.update(user_task_instance.get_data())
        CaseWorkflow.complete_user_task(task.id, data)
