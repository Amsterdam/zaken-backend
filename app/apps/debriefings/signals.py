from apps.debriefings.models import Debriefing
from apps.workflow.models import CaseWorkflow
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Debriefing, dispatch_uid="debrief_create_complete_task")
def complete_task_create_debrief(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if created:
        CaseWorkflow.complete_user_task(
            instance.case_user_task_id,
            {
                "violation": {
                    "value": instance.violation.value,
                }
            },
            wait=True,
        )
        instance.case.force_citizen_report_feedback(instance)
