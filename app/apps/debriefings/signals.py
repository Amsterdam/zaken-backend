from apps.camunda.services import CamundaService
from apps.debriefings.models import Debriefing
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(
    post_save, sender=Debriefing, dispatch_uid="debrief_create_complete_camunda_task"
)
def complete_camunda_task_create_debrief(sender, instance, created, **kwargs):
    task = False

    for camunda_id in instance.case.camunda_ids:
        task = CamundaService().get_task_by_task_name_id_and_camunda_id(
            "task_create_debrief", camunda_id
        )
        if task:
            break
    if task:
        CamundaService().complete_task(
            task["id"], {"violation": {"value": instance.violation}}
        )
