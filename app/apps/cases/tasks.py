import logging

import celery
from apps.workflow.models import CaseWorkflow
from celery import shared_task

DEFAULT_RETRY_DELAY = 2
logger = logging.getLogger(__name__)


class BaseTaskWithRetry(celery.Task):
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = DEFAULT_RETRY_DELAY


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_update_citizen_report_feedback_workflows(
    self, case_id, force_citizen_report_feedback=False
):
    from apps.cases.models import Case

    case = Case.objects.get(id=case_id)
    for caseworkflow in case.workflows.filter(
        workflow_type=CaseWorkflow.WORKFLOW_TYPE_CITIZEN_REPORT_FEEDBACK,
        completed=False,
    ):
        caseworkflow.update_workflow_data(
            {
                "force_citizen_report_feedback": {
                    "value": force_citizen_report_feedback,
                },
            }
        )

    return f"task_update_citizen_report_feedback_workflows: case with id '{case_id}' complete"
