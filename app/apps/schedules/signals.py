from apps.schedules.models import Schedule
from apps.workflow.models import CaseWorkflow
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Schedule, dispatch_uid="schedule_create_complete_task")
def complete_task_create_schedule(sender, instance, created, **kwargs):
    if created:
        CaseWorkflow.complete_user_task(instance.case_user_task_id, {})
