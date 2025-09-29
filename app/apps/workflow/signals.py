import copy
import datetime
import logging
from datetime import timezone

from apps.events.models import TaskModelEventEmitter
from apps.visits.models import Visit
from apps.workflow.models import CaseUserTask, CaseWorkflow, GenericCompletedTask
from apps.workflow.tasks import task_start_worflow
from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone as django_timezone
from SpiffWorkflow.bpmn.serializer import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.serializer.config import CAMUNDA_CONFIG
from utils.exceptions import EventEmitterExistsError

from .user_tasks import DEFAULT_USER_TASK_DUE_DATE, get_task_by_name
from .utils import convert_value_dicts_to_dot_access, get_latest_version_from_config

logger = logging.getLogger(__name__)


@receiver(pre_save, dispatch_uid="event_emitter_pre_save")
def event_emitter_pre_save(instance, **kwargs):
    if not issubclass(instance.__class__, TaskModelEventEmitter):
        return
    if kwargs.get("raw"):
        return
    cache.set("connection", "test")

    if (
        not instance.id
        and not isinstance(instance, Visit)
        and hasattr(instance, "case_user_task_id")
        and instance.case_user_task_id
        and instance.case_user_task_id != "-1"
    ):
        type_instance = instance.__class__.objects.filter(
            case_user_task_id=instance.case_user_task_id
        )
        if type_instance:
            logger.error(
                f"TaskModelEventEmitter of type '{instance.__class__.__name__}', with id '{instance.case_user_task_id}', already exists"
            )
            raise EventEmitterExistsError(
                f"TaskModelEventEmitter of type '{instance.__class__.__name__}', with id '{instance.case_user_task_id}', already exists"
            )


@receiver(pre_save, sender=CaseUserTask, dispatch_uid="case_user_task_pre_save")
def case_user_task_pre_save(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return

    now = django_timezone.now()
    d = datetime.datetime(
        year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc
    )

    if not instance.id:
        task = get_task_by_name(instance.task_name)

    try:
        task_elapse_datetime = instance.workflow.get_task_elapse_datetime(
            instance.task_id
        )
    except Exception:
        # If task is not found in workflow, just skip this
        task_elapse_datetime = None
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
            # Get task for new instances, fallback to default for existing instances
            if not instance.id:
                instance.due_date = d + (
                    task.get_due_date(instance) if task else DEFAULT_USER_TASK_DUE_DATE
                )
            else:
                # For existing instances without cached data, use default due date
                instance.due_date = d + DEFAULT_USER_TASK_DUE_DATE
    else:
        try:
            previous = CaseUserTask.objects.get(id=instance.id)
            if instance.due_date != previous.due_date:
                instance.workflow.set_task_elapse_datetime(
                    instance.task_id, instance.due_date
                )
        except CaseUserTask.DoesNotExist:
            # This can happen during bulk_create where instances have IDs but aren't saved yet
            # In this case, treat it as a new instance and set default due date
            instance.due_date = d + DEFAULT_USER_TASK_DUE_DATE


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
                        "value": (
                            "ja"
                            if reason == "leegstandsmelding_eigenaar"
                            else "default"
                        ),
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
        reg = instance.get_serializer().configure(CAMUNDA_CONFIG)
        serializer = BpmnWorkflowSerializer(registry=reg)
        serialized_wf = serializer.serialize_json(wf)
        instance.serialized_workflow_state = serialized_wf


@receiver(post_save, sender=CaseWorkflow, dispatch_uid="start_workflow")
def start_workflow(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if created:
        # Run asynchronously so lock contention triggers Celery autoretry instead of failing inline
        task_start_worflow.delay(instance.id)


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
        converted_data = convert_value_dicts_to_dot_access(data)
        converted_data.pop("mapped_form_data")
        user_task_type = get_task_by_name(task.task_name)
        user_task_instance = user_task_type(task)
        converted_data.update(user_task_instance.get_data())

        CaseWorkflow.complete_user_task(task.id, converted_data, wait=True)
