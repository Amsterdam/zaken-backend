import logging

from apps.camunda.models import GenericCompletedTask
from apps.camunda.services import CamundaService
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(
    post_save,
    sender=GenericCompletedTask,
    dispatch_uid="generic_completed_init_in_camunda",
)
def create_generic_completed_instance_in_camunda(sender, instance, created, **kwargs):
    if created:
        CamundaService().complete_task(instance.camunda_task_id, instance.variables)
