import copy
import datetime

import pytz
from apps.events.models import TaskModelEventEmitter
from apps.workflow.models import CaseUserTask, CaseWorkflow, GenericCompletedTask
from apps.workflow.tasks import task_start_worflow
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
        instance.due_date = d + (
            task.get_due_date(instance) if task else DEFAULT_USER_TASK_DUE_DATE
        )


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

        if instance.main_workflow:
            instance.data.update(
                {
                    "theme": {"value": f"theme_{instance.case.theme.snake_case_name}"},
                    "reason": {
                        "value": f"reason_{instance.case.reason.snake_case_name}"
                    },
                }
            )

        current_verion = (
            existing_main_workflows.workflow_version
            if existing_main_workflows
            else None
        )

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
        CaseWorkflow.complete_user_task(task.id, data)
