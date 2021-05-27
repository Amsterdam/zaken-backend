from apps.camunda.services import CamundaService
from apps.debriefings.models import Debriefing
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(
    post_save, sender=Debriefing, dispatch_uid="debrief_create_complete_camunda_task"
)
def complete_camunda_task_create_debrief(sender, instance, created, **kwargs):
    if created:
        CamundaService().complete_task(
            instance.camunda_task_id, {"violation": {"value": instance.violation}}
        )
