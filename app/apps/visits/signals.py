from apps.visits.models import Visit
from apps.workflow.models import CaseWorkflow
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=Visit, dispatch_uid="add_case_user_task_id_to_visit")
def add_case_user_task_id_to_visit(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return
    if not instance.id:
        task = instance.case.tasks.filter(
            task_name="task_create_visit",
            completed=False,
        ).first()
        if task:
            instance.case_user_task_id = str(task.id)
        else:
            raise Exception("No task found")


@receiver(post_save, sender=Visit, dispatch_uid="complete_task_create_visit")
def complete_task_create_visit(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if instance.case_user_task_id != "-1" and created and instance.completed:
        CaseWorkflow.complete_user_task(
            instance.case_user_task_id,
            {
                "situation": {"value": instance.situation},
                "can_next_visit_go_ahead": {"value": instance.can_next_visit_go_ahead},
            },
        )
