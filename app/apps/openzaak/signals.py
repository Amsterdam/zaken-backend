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


@receiver(
    post_save,
    sender=CaseState,
    dispatch_uid="set_result_and_create_case_instance_in_openzaak",
)
def set_resultaat_and_create_case_instance_in_openzaak(
    sender, instance, created, **kwargs
):
    # If the state of a case has changed from Toezicht to Handhaven,
    # a new case instance must be created in open-zaak because of the limitation period.
    # Toezicht has a limitation period of five years and Handhaven ten years.
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
            previous_casestate_instance = CaseState.objects.get(
                case=instance.case, status=CaseState.CaseStateChoice.TOEZICHT
            )
            # Update previous CaseState
            previous_casestate_instance.set_in_open_zaak = True
            previous_casestate_instance.save()
            # Create new case in open-zaak with zaaktype HANDHAVING
            create_open_zaak_case(
                instance.case,
                zaaktype_identificatie=settings.OPENZAAK_ZAAKTYPE_IDENTIFICATIE_HANDHAVEN,
            )
        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)


@receiver(
    post_save,
    sender=CaseState,
    dispatch_uid="set_resultaat_and_close_case_instance_in_openzaak",
)
def set_resultaat_and_close_case_instance_in_openzaak(
    sender, instance, created, **kwargs
):
    # To close a case in open-zaak a Resultaat and Status must be created.
    if (
        instance.case.case_url
        and instance.status == CaseState.CaseStateChoice.AFGESLOTEN
        and not instance.set_in_open_zaak
        and not instance.system_build
    ):
        previous_casestate_instance = CaseState.objects.filter(
            case=instance.case, status=CaseState.CaseStateChoice.HANDHAVING
        ).first()

        try:
            if previous_casestate_instance is None:
                # Case has no CaseState Handhaving so set Resultaat "Toezicht afgebroken"
                create_open_zaak_case_resultaat(
                    instance.case,
                    omschrijving_generiek=settings.OPENZAAK_RESULTAATTYPE_OMSCHRIJVING_GENERIEK_AFGEBROKEN,
                )
                # Get previous CaseState
                previous_casestate_instance = CaseState.objects.get(
                    case=instance.case, status=CaseState.CaseStateChoice.TOEZICHT
                )
            else:
                # Case has a CaseState Handhaven so set Resultaat "Handhaven uitgevoerd"
                create_open_zaak_case_resultaat(instance.case)

            # Set Status "Afsluiten" to close the case in open-zaak
            create_open_zaak_case_status(instance)

        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)
        finally:
            # Update previous CaseState Toezicht or Handhaving
            previous_casestate_instance.set_in_open_zaak = True
            previous_casestate_instance.save()
            # Update current instance of CaseState
            instance.set_in_open_zaak = True
            instance.save()


@receiver(post_save, sender=CaseDocument)
def create_case_document_instance_in_openzaak(sender, instance, created, **kwargs):
    if created:
        try:
            connect_case_and_document(instance)
        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)
