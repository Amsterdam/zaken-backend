from apps.schedules.models import Schedule
from apps.workflow.models import Workflow
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(
    post_save, sender=Schedule, dispatch_uid="schedule_create_complete_camunda_task"
)
def complete_camunda_task_create_schedule(sender, instance, created, **kwargs):
    if created:
        Workflow.complete_user_task(instance.camunda_task_id, {})
        # CamundaService().complete_task(instance.camunda_task_id)
