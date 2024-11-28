import logging

from apps.workflow.models import CaseWorkflow
from apps.workflow.tasks import task_create_citizen_report_worflow_for_case
from django.db import transaction

logger = logging.getLogger(__name__)


def complete_citizen_report_task(serializer):
    try:
        with transaction.atomic():
            citizen_report = serializer.create(serializer.validated_data)
            CaseWorkflow.complete_user_task(
                citizen_report.case_user_task_id, {}, wait=True, timeout=15
            )
            task_create_citizen_report_worflow_for_case.delay(citizen_report.id)
    except Exception as e:
        logger.error(f"Error completing task {citizen_report.case_user_task_id}: {e}")
        raise e
