from apps.camunda.services import CamundaService
from apps.visits.models import Visit
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Visit, dispatch_uid="visit_create_complete_camunda_task")
def complete_camunda_task_create_visit(sender, instance, created, **kwargs):
    task = False
    for state in instance.case.case_states.filter(end_date__isnull=True):
        task = CamundaService().get_task_by_task_name_id_and_camunda_id(
            "task_create_visit", state.case_process_id
        )
        if task:
            break

    # Legacy using camunda_ids
    if not task:
        for camunda_id in instance.case.camunda_ids:
            task = CamundaService().get_task_by_task_name_id_and_camunda_id(
                "task_create_visit", camunda_id
            )
            if task:
                break

    if task:
        CamundaService().complete_task(
            task["id"],
            {
                "situation": {"value": instance.situation},
                "can_next_visit_go_ahead": {"value": instance.can_next_visit_go_ahead},
            },
        )
