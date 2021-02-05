import logging
import sys

from apps.camunda.services import CamundaService
from apps.summons.models import Summon
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Summon, dispatch_uid="summon_init_in_camunda")
def create_summon_instance_in_camunda(sender, instance, created, **kwargs):
    if created and "test" not in sys.argv:
        pass  # pass for now
    #     camunda_id = CamundaService().start_instance()
    #     instance.camunda_id = camunda_id
    #     instance.save()


@receiver(post_save, sender=Summon)
def create_summon_instance_in_openzaak(sender, instance, created, **kwargs):
    if created and "test" not in sys.argv:
        pass  # pass for now
