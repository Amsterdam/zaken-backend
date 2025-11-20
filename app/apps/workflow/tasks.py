import copy
from time import sleep

import celery
from apps.cases.models import Case, CitizenReport
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.db import transaction

logger = get_task_logger(__name__)

DEFAULT_RETRY_DELAY = 2
MAX_RETRIES = 6

LOCK_EXPIRE = 5

TASK_PRIORITY_LOW = 1  # Periodic/maintenance tasks (low)
TASK_PRIORITY_HIGH = 9  # User-facing actions (high)


def redis_lock(lock_id):
    status = cache.add(lock_id, "lock", timeout=LOCK_EXPIRE)
    logger.info(f"REDIS_LOCK START: lock id '{lock_id}', status: {status}")
    return status


def release_lock(lock_id):
    logger.info(f"REDIS_LOCK END: lock id '{lock_id}'")
    cache.delete(lock_id)


class BaseTaskWithRetry(celery.Task):
    autoretry_for = (Exception,)
    max_retries = MAX_RETRIES
    default_retry_delay = DEFAULT_RETRY_DELAY


@shared_task(bind=True, base=BaseTaskWithRetry, priority=TASK_PRIORITY_LOW)
def task_update_workflows(self):
    from apps.workflow.models import CaseWorkflow

    workflow_instances = CaseWorkflow.objects.filter(completed=False)
    for workflow in workflow_instances:
        if workflow.has_a_timer_event_fired():
            logger.warning(
                f"task_update_workflows: workflow with id '{workflow.id}', has a timer event fired"
            )
            task_update_workflow.delay(workflow.id)
    return f"task_update_workflows complete: count '{workflow_instances.count()}'"


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_update_workflow(self, workflow_id):
    from apps.workflow.models import CaseWorkflow

    workflow_instance = CaseWorkflow.objects.get(id=workflow_id)
    if workflow_instance.get_lock():
        with transaction.atomic():
            workflow_instance.update_workflow()
        return f"task_update_workflow: update for workflow with id '{workflow_id}', complete"
    raise Exception(
        f"task_update_workflow: update for workflow with id '{workflow_id}', is busy"
    )


@shared_task(bind=True, base=BaseTaskWithRetry, priority=TASK_PRIORITY_HIGH)
def task_accept_message_for_workflow(self, workflow_id, message, extra_data):
    from apps.workflow.models import CaseWorkflow

    workflow_instance = CaseWorkflow.objects.get(id=workflow_id)
    if workflow_instance.get_lock():
        with transaction.atomic():
            workflow_instance.accept_message(message, extra_data)
            return f"task_accept_message_for_workflow: message '{message}' for workflow with id {workflow_id}, accepted"

    raise Exception(
        f"task_accept_message_for_workflow: message '{message}' for workflow with id '{workflow_id}'', is busy"
    )


@shared_task(bind=True, base=BaseTaskWithRetry, priority=TASK_PRIORITY_HIGH)
def task_start_subworkflow(self, subworkflow_name, parent_workflow_id, extra_data={}):
    from apps.workflow.models import CaseWorkflow

    parent_workflow = CaseWorkflow.objects.get(id=parent_workflow_id)
    with transaction.atomic():
        data = copy.deepcopy(parent_workflow.get_data())
        data.update(extra_data)
        subworkflow = CaseWorkflow.objects.create(
            case=parent_workflow.case,
            parent_workflow=parent_workflow,
            workflow_type=subworkflow_name,
            data=data,
        )

    return f"task_start_subworkflow:  subworkflow id '{subworkflow.id}', for parent workflow with id '{parent_workflow_id}', created"


@shared_task(bind=True, base=BaseTaskWithRetry, priority=TASK_PRIORITY_HIGH)
def task_create_main_worflow_for_case(self, case_id, data={}):
    from apps.workflow.models import CaseWorkflow

    case = Case.objects.get(id=case_id)
    # Idempotency: if a main workflow already exists for this case, do nothing
    existing = CaseWorkflow.objects.filter(case=case, main_workflow=True).first()
    if existing:
        return f"task_start_main_worflow_for_case: main workflow id '{existing.id}' already exists for case '{case_id}', skipping"
    with transaction.atomic():
        workflow_instance = CaseWorkflow.objects.create(
            case=case,
            workflow_type=settings.DEFAULT_WORKFLOW_TYPE,
            main_workflow=True,
            workflow_message_name="main_process",
            data=data,
        )

    return f"task_start_main_worflow_for_case: workflow id '{workflow_instance.id}', for case with id '{case_id}', created"


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_create_citizen_report_worflow_for_case(self, citizen_report_id, data={}):
    from apps.workflow.models import CaseWorkflow

    citizen_report = CitizenReport.objects.get(id=citizen_report_id)

    periods_setting = next(
        iter(
            [
                periods_setting
                for periods_setting in settings.CITIZEN_REPORT_FEEDBACK_PERIODS
                if citizen_report.case.theme.id in periods_setting.get("themes", [])
            ]
        ),
        {
            "periods": [
                settings.CITIZEN_REPORT_FEEDBACK_DEFAULT_FIRST_PERIOD,
                settings.CITIZEN_REPORT_FEEDBACK_DEFAULT_SECOND_PERIOD,
            ]
        },
    )
    data.update(
        {
            "names": {"value": citizen_report.get_status_information()},
            "force_citizen_report_feedback": {
                "value": citizen_report.case.force_citizen_report_feedback()
            },
            "CITIZEN_REPORT_FEEDBACK_FIRST_PERIOD": periods_setting.get("periods")[0],
            "CITIZEN_REPORT_FEEDBACK_SECOND_PERIOD": periods_setting.get("periods")[1],
        }
    )

    with transaction.atomic():
        workflow_instance = CaseWorkflow.objects.create(
            case=citizen_report.case,
            workflow_type="citizen_report_feedback",
            data=data,
        )

    return f"task_create_citizen_report_worflow_for_case: workflow id '{workflow_instance.id}', for citizen_report with id '{citizen_report_id}', created"


@shared_task(bind=True, base=BaseTaskWithRetry, priority=TASK_PRIORITY_HIGH)
def task_start_worflow(self, worklow_id):
    from apps.workflow.models import CaseWorkflow

    workflow_instance = CaseWorkflow.objects.get(id=worklow_id)
    if workflow_instance.get_lock():
        with transaction.atomic():
            workflow_instance.start()
            return f"task_start_worflow: workflow id '{worklow_id}', started"

    raise Exception(f"task_start_worflow: workflow id '{worklow_id}', is busy")


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_reset_subworkflow(self, worklow_id, subworkflow):
    from apps.workflow.models import CaseWorkflow

    workflow_instance = CaseWorkflow.objects.get(id=worklow_id)
    if workflow_instance.get_lock():
        with transaction.atomic():
            sleep(2)
            workflow_instance.reset_subworkflow(subworkflow, test=False)
            return f"task_reset_subworkflow: workflow id '{worklow_id}', started"

    raise Exception(f"task_reset_subworkflow: workflow id '{worklow_id}', is busy")


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_wait_for_workflows_and_send_message(self, workflow_id, message, extra_data={}):
    from apps.workflow.models import CaseWorkflow

    workflow_instance = CaseWorkflow.objects.get(id=workflow_id)

    if workflow_instance.get_lock():
        main_workflow = CaseWorkflow.objects.filter(
            case=workflow_instance.case, main_workflow=True
        ).first()

        if hasattr(main_workflow.__class__, f"handle_{message}") and callable(
            getattr(main_workflow.__class__, f"handle_{message}")
        ):
            data = getattr(main_workflow, f"handle_{message}")(workflow_instance)

            if data:
                task_accept_message_for_workflow.delay(main_workflow.id, message, data)

        return f"task_wait_for_workflows_and_send_message: message '{message}' for workflow with id '{workflow_id}', completed"
    raise Exception(
        f"task_wait_for_workflows_and_send_message: message '{message}' for workflow with id '{workflow_id}', is busy"
    )


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_script_wait(self, workflow_id, message, extra_data={}):
    from apps.workflow.models import CaseWorkflow

    workflow_instance = CaseWorkflow.objects.get(id=workflow_id)

    if hasattr(workflow_instance.__class__, f"handle_{message}") and callable(
        getattr(workflow_instance.__class__, f"handle_{message}")
    ):
        data = getattr(workflow_instance, f"handle_{message}")(extra_data)

        if data:
            task_accept_message_for_workflow.delay(workflow_instance.id, message, data)

    return f"task_script_wait: message '{message}' for workflow with id '{workflow_id}', completed"


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_complete_worflow(self, worklow_id, data):
    from apps.workflow.models import CaseWorkflow

    workflow_instance = CaseWorkflow.objects.get(id=worklow_id)
    if workflow_instance.get_lock():
        with transaction.atomic():
            if (
                workflow_instance.parent_workflow
                and workflow_instance.parent_workflow.workflow_type
                == CaseWorkflow.WORKFLOW_TYPE_DIRECTOR
            ):
                workflow_instance.parent_workflow.accept_message(
                    f"resume_after_{workflow_instance.workflow_type}",
                    data,
                )

        return f"task_complete_worflow: workflow id '{worklow_id}', completed"
    raise Exception(f"task_complete_worflow: workflow id '{worklow_id}', is busy")


@shared_task(bind=True, base=BaseTaskWithRetry, priority=TASK_PRIORITY_HIGH)
def task_complete_user_task_and_create_new_user_tasks(self, task_id, data={}):
    import time

    from apps.workflow.models import CaseUserTask

    # Log retry attempts
    if self.request.retries > 0:
        logger.warning(
            f"[TIMING] Celery task RETRY #{self.request.retries} for task_id {task_id} "
            f"(attempt {self.request.retries + 1}/{MAX_RETRIES + 1})"
        )

    task_start = time.time()
    logger.info(f"[TIMING] Celery task started for task_id {task_id}")

    task = CaseUserTask.objects.filter(id=task_id, completed=False).first()
    if not task:
        logger.warning(f"[TIMING] Task {task_id} not found or already completed")
        return f"task_complete_user_task_and_create_new_user_tasks: task '{task_id}' not found or already completed, skipping"

    lock_start = time.time()
    if task.workflow.get_lock():
        lock_duration = time.time() - lock_start
        logger.info(
            f"[TIMING] Lock acquired for workflow {task.workflow.id} in {lock_duration:.2f}s"
        )

        complete_start = time.time()
        task.workflow.complete_user_task_and_create_new_user_tasks(task.task_id, data)
        complete_duration = time.time() - complete_start
        total_duration = time.time() - task_start

        logger.info(
            f"[TIMING] Celery task completed: task '{task.task_name}' for workflow {task.workflow.id} "
            f"in {complete_duration:.2f}s (total: {total_duration:.2f}s)"
        )
        return f"task_complete_user_task_and_create_new_user_tasks: complete task with name '{task.task_name}' for workflow with id '{task.workflow.id}', is completed"

    lock_duration = time.time() - lock_start
    logger.warning(
        f"[TIMING] Failed to acquire lock for workflow {task.workflow.id} after {lock_duration:.2f}s"
    )
    raise Exception(
        f"task_complete_user_task_and_create_new_user_tasks: complete task with name '{task.task_name}' for workflow with id '{task.workflow.id}', is busy"
    )
