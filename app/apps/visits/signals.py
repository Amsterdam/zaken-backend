from apps.camunda.services import CamundaService
from apps.visits.models import Visit
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Visit, dispatch_uid="visit_create_complete_camunda_task")
def complete_camunda_task_create_visit(sender, instance, created, **kwargs):
    task = CamundaService().get_task_by_task_name_id_and_camunda_id(
        "task_create_visit", instance.case.camunda_id
    )
    CamundaService().complete_task(
        task["id"], {"situation": {"value": instance.situation}}
    )
