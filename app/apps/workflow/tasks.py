import copy

import celery
from config.celery import app as celery_app
from django.conf import settings
from django.db import DatabaseError, transaction

from . import exceptions
from .utils import get_initial_data_from_config

DEFAULT_RETRY_DELAY = 10


class BaseTaskWithRetry(celery.Task):
    autoretry_for = (exceptions.ServerError, Exception)
    retry_kwargs = {"max_retries": 2}
    retry_backoff = True
    default_retry_delay = DEFAULT_RETRY_DELAY


@celery_app.task(bind=True)
def update_workflows(self):
    from apps.workflow.models import CaseWorkflow

    for workflows in CaseWorkflow.objects.all():
        workflows.update_workflow()
    return "Update workflows complete"


@celery_app.task(bind=True)
def accept_message_for_workflow(self, workflow_id, message, extra_data):
    from apps.workflow.models import CaseWorkflow

    workflow = CaseWorkflow.objects.filter(id=workflow_id).first()
    if not workflow:
        return "workflow not found: %s" % workflow_id

    workflow.accept_message(message, extra_data)

    return "workflow: %s, message: %s" % (
        workflow_id,
        message,
    )


def create_workflow_for_case(case):
    from apps.workflow.models import CaseWorkflow

    with transaction.atomic():
        workflow_instance = CaseWorkflow.objects.create(
            case=case,
            workflow_type=settings.DEFAULT_WORKFLOW_TYPE,
            main_workflow=True,
        )
        workflow_instance.message(
            "main_process",
            settings.DEFAULT_SCHEDULE_ACTIONS[0],
            "status_name",
            {
                "status_name": settings.DEFAULT_SCHEDULE_ACTIONS[0],
            },
        )


def start_case_with_workflow(case_data, address):
    from apps.cases.models import Case

    # make sure case and workflow are created together or not
    try:
        with transaction.atomic():
            case = Case.objects.create(**case_data, address=address)
            create_workflow_for_case(case)
        return case
    except DatabaseError:
        raise exceptions.ServerError()


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def task_start_case_workflow(self, case_data, address):

    case = start_case_with_workflow(case_data, address)

    return f"case with id '{case.id}' created"


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def task_start_workflow_for_existing_case(self, case_id):
    from apps.cases.models import Case

    case = Case.objects.get(id=case_id)

    create_workflow_for_case(case)

    return f"case with id '{case.id}' created"


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def task_start_subworkflow(self, subworkflow_name, parent_workflow_id):
    from apps.workflow.models import CaseWorkflow

    parent_workflow = CaseWorkflow.objects.get(id=parent_workflow_id)

    data = get_initial_data_from_config(
        parent_workflow.case.theme.name, subworkflow_name
    )
    parent_data = copy.deepcopy(parent_workflow.get_data())
    data.update(parent_data)

    with transaction.atomic():
        subworkflow = CaseWorkflow.objects.create(
            case=parent_workflow.case,
            parent_workflow=parent_workflow,
            workflow_type=subworkflow_name,
        )
        subworkflow.set_initial_data(data)
