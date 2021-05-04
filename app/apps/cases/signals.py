import json
import logging
import sys

from apps.cases.models import Case
from apps.cases.tasks import start_camunda_instance
from apps.openzaak.helpers import create_open_zaak_case
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Case, dispatch_uid="case_init_in_camunda")
def create_case_instance_in_camunda(sender, instance, created, **kwargs):
    if created and "test" not in sys.argv:
        request_body = json.dumps(
            {
                "variables": {
                    "zaken_access_token": {
                        "value": settings.CAMUNDA_SECRET_KEY,
                        "type": "String",
                    },
                    "case_identification": {
                        "value": instance.id,
                        "type": "String",
                    },
                    "endpoint": {
                        "value": settings.ZAKEN_CONTAINER_HOST,
                        "type": "String",
                    },
                },
            }
        )
        task = start_camunda_instance.s(
            identification=instance.id, request_body=request_body
        ).delay
        transaction.on_commit(task)


@receiver(post_save, sender=Case)
def create_case_instance_in_openzaak(sender, instance, created, **kwargs):
    if created and "test" not in sys.argv:
        try:
            create_open_zaak_case(
                identification=instance.id, description=instance.description
            )
        except Exception as e:
            logger.error(e)
