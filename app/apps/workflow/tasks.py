import copy
import logging

import celery
from celery import shared_task
from django.conf import settings
from django.db import DatabaseError, transaction

from . import exceptions

DEFAULT_RETRY_DELAY = 10
logger = logging.getLogger(__name__)


class BaseTaskWithRetry(celery.Task):
    autoretry_for = (exceptions.ServerError, Exception, DatabaseError)
    retry_kwargs = {"max_retries": 2}
    retry_backoff = True
    default_retry_delay = DEFAULT_RETRY_DELAY


@shared_task(bind=True, default_retry_delay=DEFAULT_RETRY_DELAY)
def task_update_workflows(self):
    from apps.workflow.models import CaseWorkflow

    for workflow in CaseWorkflow.objects.filter(completed=False):
        task_update_workflow.delay(workflow.id)
    return "task_update_workflows complete"


@shared_task(bind=True, default_retry_delay=DEFAULT_RETRY_DELAY)
def task_update_workflow(self, workflow_id):
    from apps.workflow.models import CaseWorkflow

    try:
        workflow = CaseWorkflow.objects.get(id=workflow_id)
        with transaction.atomic():
            workflow.update_workflow()
    except Exception as exception:
        logger.error(
            f"ERROR: task_update_workflows: for workflow with id '{workflow_id}', {str(exception)}"
        )
        self.retry(exc=exception)

    return (
        f"task_update_workflow: update for workflow with id '{workflow_id}', complete"
    )


@shared_task(bind=True, default_retry_delay=DEFAULT_RETRY_DELAY)
def task_accept_message_for_workflow(self, workflow_id, message, extra_data):
    from apps.workflow.models import CaseWorkflow

    try:
        workflow = CaseWorkflow.objects.get(id=workflow_id)
        with transaction.atomic():
            workflow.accept_message(message, extra_data)
    except Exception as exception:
        logger.error(
            f"ERROR: task_accept_message_for_workflow: for workflow with id '{workflow_id}', with message '{message}', {str(exception)}"
        )
        self.retry(exc=exception)

    return f"task_accept_message_for_workflow: message '{message}' for workflow with id {workflow_id}, excepted"


@shared_task(bind=True, default_retry_delay=DEFAULT_RETRY_DELAY)
def task_start_subworkflow(self, subworkflow_name, parent_workflow_id):
    from apps.workflow.models import CaseWorkflow

    try:
        parent_workflow = CaseWorkflow.objects.get(id=parent_workflow_id)
        with transaction.atomic():
            data = copy.deepcopy(parent_workflow.get_data())

            subworkflow = CaseWorkflow.objects.create(
                case=parent_workflow.case,
                parent_workflow=parent_workflow,
                workflow_type=subworkflow_name,
                data=data,
            )

    except Exception as exception:
        logger.error(
            f"ERROR: task_start_subworkflow: '{subworkflow_name}', parent workflow id '{parent_workflow_id}', {str(exception)}"
        )
        self.retry(exc=exception)

    return f"task_start_subworkflow:  subworkflow id '{subworkflow.id}', for parent workflow with id '{parent_workflow_id}', created"


@shared_task(bind=True, default_retry_delay=DEFAULT_RETRY_DELAY)
def task_create_main_worflow_for_case(self, case_id):
    from apps.cases.models import Case
    from apps.workflow.models import CaseWorkflow

    try:
        case = Case.objects.get(id=case_id)
        with transaction.atomic():
            workflow_instance = CaseWorkflow.objects.create(
                case=case,
                workflow_type=settings.DEFAULT_WORKFLOW_TYPE,
                main_workflow=True,
                workflow_message_name="main_process",
            )

    except Exception as exception:
        logger.error(
            f"ERROR: task_start_main_worflow_for_case: case id '{case_id}', {str(exception)}"
        )
        self.retry(exc=exception)

    return f"task_start_main_worflow_for_case: workflow id '{workflow_instance.id}', for case with id '{case.id}', created"


@shared_task(bind=True, default_retry_delay=DEFAULT_RETRY_DELAY)
def task_start_worflow(self, worklow_id):
    from apps.workflow.models import CaseWorkflow

    try:
        case_workflow = CaseWorkflow.objects.get(id=worklow_id)
        with transaction.atomic():
            case_workflow.start()

    except Exception as exception:
        logger.error(
            f"ERROR: task_start_worflow: worklow id '{worklow_id}', {str(exception)}"
        )
        self.retry(exc=exception)

    return f"task_start_worflow: workflow id '{worklow_id}', started"


@shared_task(bind=True, default_retry_delay=DEFAULT_RETRY_DELAY)
def task_complete_worflow(self, worklow_id, data):
    from apps.workflow.models import CaseWorkflow

    try:
        case_workflow = CaseWorkflow.objects.get(id=worklow_id)
        with transaction.atomic():
            if (
                case_workflow.parent_workflow
                and case_workflow.parent_workflow.workflow_type
                == CaseWorkflow.WORKFLOW_TYPE_DIRECTOR
            ):
                case_workflow.parent_workflow.accept_message(
                    f"resume_after_{case_workflow.workflow_type}",
                    data,
                )
            case_workflow.completed = True
            case_workflow.save()
            # maybe delete workflow object when completed
            # self.delete()

    except Exception as exception:
        logger.error(
            f"ERROR: task_complete_worflow: worklow id '{worklow_id}', {str(exception)}"
        )
        self.retry(exc=exception)

    return f"task_complete_worflow: workflow id '{worklow_id}', completed"
