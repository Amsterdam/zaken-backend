from apps.quick_decisions.models import QuickDecision
from apps.summons.models import Summon
from apps.workflow.models import CaseWorkflow
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(
    post_save, sender=QuickDecision, dispatch_uid="quick_decision_create_complete_task"
)
def complete_task_create_quick_decision(sender, instance, created, **kwargs):
    """
    Complete task after quick_decision is created
    """
    if kwargs.get("raw"):
        return
    if created:
        task = CaseWorkflow.get_task_by_task_id(instance.case_user_task_id)
        summon = Summon.objects.filter(
            id=task.workflow.get_data().get("summon_id", {}).get("value", 0)
        ).first()

        if summon:
            instance.summon = summon
            instance.save()

        CaseWorkflow.complete_user_task(
            task.id,
            {
                "type_besluit": {"value": instance.quick_decision_type.workflow_option},
            },
            wait=True,
        )
