import logging

from apps.workflow.models import CaseWorkflow
from django.db import transaction

logger = logging.getLogger(__name__)


def complete_task_create_visit(serializer):
    with transaction.atomic():
        try:
            visit = serializer.create(serializer.validated_data)
            if visit.completed:
                task = visit.case.tasks.filter(
                    task_name="task_create_visit",
                    completed=False,
                    id=int(visit.case_user_task_id),
                ).first()
                if task:
                    CaseWorkflow.complete_user_task(
                        visit.case_user_task_id,
                        {
                            "situation": {"value": visit.situation},
                            "can_next_visit_go_ahead": {
                                "value": visit.can_next_visit_go_ahead
                            },
                        },
                        wait=True,
                    )
        except Exception as e:
            logger.error(f"Error completing task complete_task_create_visite: {e}")
            raise e
