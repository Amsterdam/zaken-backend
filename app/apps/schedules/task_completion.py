import logging

from apps.workflow.models import CaseWorkflow
from django.db import transaction

logger = logging.getLogger(__name__)


def complete_task_create_schedule(serializer):
    with transaction.atomic():
        try:
            schedule = serializer.create(serializer.validated_data)
            CaseWorkflow.complete_user_task(schedule.case_user_task_id, {}, wait=True)
        except Exception as e:
            logger.error(f"Error completing task complete_task_create_schedule: {e}")
            raise e
