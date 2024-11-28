import logging

from apps.summons.models import Summon
from apps.workflow.models import CaseWorkflow
from django.db import transaction

logger = logging.getLogger(__name__)


def complete_task_create_quick_decision(serializer):
    with transaction.atomic():
        try:
            quick_decision = serializer.create(serializer.validated_data)
            task = CaseWorkflow.get_task_by_task_id(quick_decision.case_user_task_id)
            summon = Summon.objects.filter(
                id=task.workflow.get_data().get("summon_id", {}).get("value", 0)
            ).first()

            if summon:
                quick_decision.summon = summon
                quick_decision.save()

            CaseWorkflow.complete_user_task(
                task.id,
                {
                    "type_besluit": {
                        "value": quick_decision.quick_decision_type.workflow_option
                    },
                },
                wait=True,
            )
        except Exception as e:
            logger.error(f"Error while completing task for quick_decision: {e}")
            raise e
