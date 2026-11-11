import base64
import logging
from io import BytesIO

import celery
from apps.permits.api_queries_powerbrowser import get_is_bed_and_breakfast_for_bag_id
from apps.workflow.models import CaseWorkflow
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

DEFAULT_RETRY_DELAY = 2
logger = logging.getLogger(__name__)


class BaseTaskWithRetry(celery.Task):
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = DEFAULT_RETRY_DELAY


@shared_task
def task_import_leegstand(file_base64, user_id, theme_id, reason_id, subject_ids, project_id, jump_to):
    from utils.bulk_leegstand_importer import BulkLeegstandImporter

    user = get_user_model().objects.get(pk=user_id)
    # A partially completed import cannot safely be retried automatically.
    with BytesIO(base64.b64decode(file_base64, validate=True)) as file:
        return BulkLeegstandImporter(
            file,
            user,
            theme= theme_id,
            reason= reason_id,
            subjects= subject_ids,
            project= project_id,
            jump_to=jump_to,
            dry_run=False,
        ).import_from_file()


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


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_update_is_bed_and_breakfast_cases(self):
    from apps.cases.models import Case

    cases_to_update = []
    updated_at = timezone.now()
    open_vakantieverhuur_cases = Case.objects.filter(
        theme__name=settings.VAKANTIEVERHUUR_THEME,
        end_date__isnull=True,
        address__bag_id__isnull=False,
    ).select_related("address")

    for case in open_vakantieverhuur_cases.iterator():
        is_bed_and_breakfast = get_is_bed_and_breakfast_for_bag_id(case.address.bag_id)
        if case.is_bed_and_breakfast == is_bed_and_breakfast:
            continue

        case.is_bed_and_breakfast = is_bed_and_breakfast
        case.last_updated = updated_at
        cases_to_update.append(case)

    if cases_to_update:
        Case.objects.bulk_update(
            cases_to_update,
            ["is_bed_and_breakfast", "last_updated"],
        )

    return (
        "task_update_is_bed_and_breakfast_cases: updated "
        f"{len(cases_to_update)} cases"
    )
