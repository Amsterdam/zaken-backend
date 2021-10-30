import copy
import datetime

from apps.workflow.models import (
    DEFAULT_USER_TASK_DUE_DATE,
    USER_TASKS,
    CaseUserTask,
    CaseWorkflow,
    GenericCompletedTask,
)
from apps.workflow.tasks import task_start_worflow
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow

from .utils import get_latest_version_from_config


@receiver(pre_save, sender=CaseUserTask, dispatch_uid="case_user_task_pre_save")
def case_user_task_pre_save(sender, instance, **kwargs):
    if not instance.id:
        now = datetime.datetime.now()
        d = datetime.datetime(year=now.year, month=now.month, day=now.day)
        instance.due_date = d + USER_TASKS.get(instance.task_name, {}).get(
            "due_date", DEFAULT_USER_TASK_DUE_DATE
        )


@receiver(pre_save, sender=CaseWorkflow, dispatch_uid="case_workflow_pre_save")
def case_workflow_pre_save(sender, instance, **kwargs):
    if not instance.id:
        if instance.main_workflow:
            existing_main_workflows = CaseWorkflow.objects.filter(
                case=instance.case,
                main_workflow=True,
            )
            if existing_main_workflows:
                raise Exception("A main workflow for this case already exists")

        instance.data = instance.data if isinstance(instance.data, dict) else {}

        (
            instance.workflow_theme_name,
            instance.workflow_version,
        ) = get_latest_version_from_config(
            instance.case.theme.name,
            instance.workflow_type,
        )
        workflow_spec = instance.get_workflow_spec()
        wf = BpmnWorkflow(workflow_spec)
        wf = instance.get_serializer().serialize_workflow(wf, include_spec=False)
        instance.serialized_workflow_state = wf


@receiver(post_save, sender=CaseWorkflow, dispatch_uid="start_workflow")
def start_workflow(sender, instance, created, **kwargs):
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
    task = CaseUserTask.objects.filter(id=instance.case_user_task_id).first()
    if created and task:
        data = copy.deepcopy(instance.variables)
        data.pop("mapped_form_data")
        task.workflow.complete_user_task_and_create_new_user_tasks(task.task_id, data)
