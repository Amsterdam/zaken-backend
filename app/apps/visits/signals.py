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
            type_instance = Visit.objects.filter(case_user_task_id=str(task.id))
            if type_instance:
                raise Exception(
                    f"TaskModelEventEmitter of type '{instance.__class__.__name__}', with '{instance.case_user_task_id}', already exists"
                )
            else:
                instance.case_user_task_id = str(task.id)
        else:
            raise Exception("No task found")


@receiver(post_save, sender=Visit, dispatch_uid="complete_task_create_visit")
def complete_task_create_visit(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if instance.case_user_task_id != "-1" and created:
        CaseWorkflow.complete_user_task(
            instance.case_user_task_id,
            {
                "situation": {"value": instance.situation},
                "can_next_visit_go_ahead": {"value": instance.can_next_visit_go_ahead},
            },
        )
