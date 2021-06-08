import logging
import sys

from apps.camunda.services import CamundaService
from apps.cases.models import Case, CitizenReport
from apps.cases.tasks import start_camunda_instance
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Case, dispatch_uid="case_init_in_camunda")
def create_case_instance_in_camunda(sender, instance, created, **kwargs):
    if created and "test" not in sys.argv:
        request_body = {
            "variables": {
                "zaken_access_token": {
                    "value": settings.CAMUNDA_SECRET_KEY,
                    "type": "String",
                },
                "case_identification": {
                    "value": str(instance.id),
                    "type": "String",
                },
                "endpoint": {
                    "value": settings.ZAKEN_CONTAINER_HOST,
                    "type": "String",
                },
                "status_name": {
                    "value": settings.DEFAULT_SCHEDULE_ACTIONS,
                    "type": "String",
                },
            },
        }
        start_camunda_instance(identification=instance.id, request_body=request_body)


# @receiver(post_save, sender=Case)
# def create_case_instance_in_openzaak(sender, instance, created, **kwargs):
#     if created and "test" not in sys.argv:
#         try:
#             create_open_zaak_case(
#                 identification=instance.id, description=instance.description
#             )
#         except Exception as e:
#             logger.error(e)


@receiver(post_save, sender=CitizenReport, dispatch_uid="complete_citizen_report_task")
def complete_citizen_report_task(sender, instance, created, **kwargs):
    if instance.camunda_task_id != "-1" and created:
        CamundaService().complete_task(
            instance.camunda_task_id,
        )
