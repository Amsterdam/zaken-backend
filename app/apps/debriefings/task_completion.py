import logging

from apps.workflow.models import CaseWorkflow
from django.db import transaction

logger = logging.getLogger(__name__)


def complete_task_create_debrief(serializer):
    with transaction.atomic():
        debrief = serializer.create(serializer.validated_data)
        try:
            CaseWorkflow.complete_user_task(
                debrief.case_user_task_id,
                {
                    "violation": {
                        "value": debrief.violation,
                    }
                },
                wait=True,
            )
        except Exception as e:
            logger.error(f"Error completing task {debrief.case_user_task_id}: {e}")
            raise e
