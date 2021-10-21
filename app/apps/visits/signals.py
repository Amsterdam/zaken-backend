from apps.visits.models import Visit
from apps.workflow.models import CaseWorkflow
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Visit, dispatch_uid="complete_task_create_visit")
def complete_task_create_visit(sender, instance, created, **kwargs):
    if instance.case_user_task_id != "-1" and created:
        CaseWorkflow.complete_user_task(
            instance.case_user_task_id,
            {
                "situation": {"value": instance.situation},
                "can_next_visit_go_ahead": {"value": instance.can_next_visit_go_ahead},
            },
        )
