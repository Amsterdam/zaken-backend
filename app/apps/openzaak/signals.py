import logging

from apps.cases.models import Case, CaseDocument, CaseState
from apps.openzaak.helpers import (
    connect_case_and_document,
    create_open_zaak_case,
    create_open_zaak_case_status,
    test_case_status_in_helpers,
    update_open_zaak_case,
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from zds_client.client import ClientError

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Case)
def create_case_instance_in_openzaak(sender, instance, created, **kwargs):
    if not instance.case_url:
        try:
            create_open_zaak_case(instance)
        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)
    else:
        try:
            update_open_zaak_case(instance)
        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)


@receiver(post_save, sender=CaseState)
def create_case_state_instance_in_openzaak(sender, instance, created, **kwargs):
    test_case_status_in_helpers()
    print("=> create_case_state_instance_in_openzaak")
    if (
        instance.case.case_url
        and not instance.set_in_open_zaak
        and not instance.system_build
    ):
        try:
            pass
            # create_open_zaak_case_status(instance)
        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)


@receiver(post_save, sender=CaseDocument)
def create_case_document_instance_in_openzaak(sender, instance, created, **kwargs):
    if created:
        try:
            connect_case_and_document(instance)
        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)
