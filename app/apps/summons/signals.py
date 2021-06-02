import logging
import sys

from apps.summons.models import Summon
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Summon)
def create_summon_instance_in_openzaak(sender, instance, created, **kwargs):
    if created and "test" not in sys.argv:
        pass  # pass for now
