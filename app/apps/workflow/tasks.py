import copy
import logging

import celery
from config.celery import app as celery_app
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


@celery_app.task(bind=True)
def task_update_workflows(self):
    from apps.workflow.models import CaseWorkflow

    for workflow in CaseWorkflow.objects.all():
        try:
            workflow.update_workflow()
        except Exception as e:
            logger.error(
                f"ERROR: task_update_workflows: for workflow with id '{workflow.id}', {str(e)}"
            )
    return "task_update_workflows complete"


@celery_app.task(bind=True)
def task_update_workflow(self, workflow_id):
    from apps.workflow.models import CaseWorkflow

    try:
        workflow = CaseWorkflow.objects.get(id=workflow_id)
        workflow.update_workflow()
    except Exception as e:
        logger.error(
            f"ERROR: task_update_workflows: for workflow with id '{workflow_id}', {str(e)}"
        )

    return (
        f"task_update_workflow: update for workflow with id '{workflow_id}', complete"
    )


@celery_app.task(bind=True)
def task_accept_message_for_workflow(self, workflow_id, message, extra_data):
    from apps.workflow.models import CaseWorkflow

    workflow = CaseWorkflow.objects.filter(id=workflow_id).first()
    if not workflow:
        return (
            f"task_accept_message_for_workflow: workflow id '{workflow_id}' not found"
        )
    workflow.accept_message(message, extra_data)

    return f"task_accept_message_for_workflow: message '{message}' for workflow with id {workflow_id}, excepted"


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def task_start_workflow_for_existing_case(self, case_id):
    from apps.cases.models import Case
    from apps.workflow.models import CaseWorkflow

    case = Case.objects.get(id=case_id)

    try:
        with transaction.atomic():
            workflow_instance = CaseWorkflow.objects.create(
                case=case,
                workflow_type=settings.DEFAULT_WORKFLOW_TYPE,
                main_workflow=True,
                workflow_message_name="main_process",
            )
            workflow_instance.start()

    except Exception as e:
        logger.error(
            f"ERROR: task_start_workflow_for_existing_case: case id '{case_id}', {str(e)}"
        )
        raise Exception(str(e))

    return f"task_start_workflow_for_existing_case: workflow id '{workflow_instance.id}', for case with id '{case.id}', created"


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def task_start_subworkflow(self, subworkflow_name, parent_workflow_id):
    from apps.workflow.models import CaseWorkflow

    try:
        # with transaction.atomic():
        parent_workflow = CaseWorkflow.objects.get(id=parent_workflow_id)

        data = copy.deepcopy(parent_workflow.get_data())

        subworkflow = CaseWorkflow.objects.create(
            case=parent_workflow.case,
            parent_workflow=parent_workflow,
            workflow_type=subworkflow_name,
        )

        subworkflow.start(data)

    except Exception as e:
        logger.error(
            f"ERROR: task_start_subworkflow: '{subworkflow_name}', parent workflow id '{parent_workflow_id}', {str(e)}"
        )
        raise Exception(str(e))

    return f"task_start_subworkflow:  subworkflow id '{subworkflow.id}', for parent workflow with id '{parent_workflow_id}', created"
