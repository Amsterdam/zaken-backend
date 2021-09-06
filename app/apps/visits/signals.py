from apps.visits.models import Visit
from apps.workflow.models import Workflow
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Visit, dispatch_uid="visit_create_complete_camunda_task")
def complete_camunda_task_create_visit(sender, instance, created, **kwargs):
    print(instance)
    if created and instance.task:
        Workflow.complete_user_task(
            instance.task.id,
            {
                "situation": {"value": instance.situation},
                "can_next_visit_go_ahead": {"value": instance.can_next_visit_go_ahead},
            },
        )
