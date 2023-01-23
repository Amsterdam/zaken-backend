import logging

from apps.cases.models import Case, CaseDocument, CaseState
from apps.openzaak.helpers import (
    connect_case_and_document,
    create_open_zaak_case,
    create_open_zaak_case_resultaat,
    create_open_zaak_case_status,
    update_open_zaak_case,
)
from django.conf import settings
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


@receiver(
    post_save, sender=CaseState, dispatch_uid="create_case_state_instance_in_openzaak"
)
def create_case_state_instance_in_openzaak(sender, instance, created, **kwargs):
    print("=> SIGNAL RECEIVED: sender=CaseState", instance)
    # If case state changed to Handhaving set Resultaat "Toezicht uitgevoerd", Status and open a new Zaak in open-zaak
    # TODO: Nu wordt CaseState Handhaving gezet (set_in_open_zaak=True),
    # maar dat zou de vorige CaseState(Toezicht) moeten zijn
    if (
        instance.case.case_url
        and instance.status == CaseState.CaseStateChoice.HANDHAVING
        and not instance.set_in_open_zaak
        and not instance.system_build
    ):
        try:
            # Set Resultaat "Toezicht uitgevoerd"
            create_open_zaak_case_resultaat(instance.case)
            # Set Status "Afsluiten" to close the case in open-zaak
            create_open_zaak_case_status(instance)
            # Get previous CaseState
            previous_casestate = CaseState.objects.get(
                case=instance.case, status=CaseState.CaseStateChoice.TOEZICHT
            )
            # Update previous CaseState
            previous_casestate.set_in_open_zaak = True
            previous_casestate.save()
            # Create new case in open-zaak with zaaktype HANDHAVING
            case_instance = Case.objects.get(id=instance.case.case_id)
            create_open_zaak_case(
                case_instance,
                zaaktype_identificatie=settings.OPENZAAK_ZAAKTYPE_IDENTIFICATIE_HANDHAVEN,
            )
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
