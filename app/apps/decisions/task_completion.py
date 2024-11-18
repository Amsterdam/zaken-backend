import logging

from apps.summons.models import Summon
from apps.workflow.models import CaseWorkflow
from django.db import transaction

logger = logging.getLogger(__name__)


def update_decision_with_summon(serializer):
    with transaction.atomic():
        try:
            decision = serializer.create(serializer.validated_data)
            task = CaseWorkflow.get_task_by_task_id(decision.case_user_task_id)
            summon = Summon.objects.filter(
                id=task.workflow.get_data().get("summon_id", {}).get("value", 0)
            ).first()

            data = {
                "type_besluit": {"value": decision.decision_type.workflow_option},
            }
            if summon:
                decision.summon = summon
                decision.save()
                names = ", ".join([person.__str__() for person in summon.persons.all()])
                data.update(
                    {
                        "names": {"value": f"{names}: {decision.decision_type.name}"},
                    }
                )
            CaseWorkflow.complete_user_task(task.id, data, wait=False)
        except Exception as e:
            logger.error(f"Error while completing task for decision: {e}")
            raise e
