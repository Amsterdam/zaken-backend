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
    # else:
    #     try:
    #         update_open_zaak_case(instance)
    #     except ClientError as e:
    #         logger.error(e)
    #     except Exception as e:
    #         logger.exception(e)


@receiver(
    post_save, sender=CaseState, dispatch_uid="create_case_state_instance_in_openzaak"
)
def create_case_state_instance_in_openzaak(sender, instance, created, **kwargs):
    print("=> SIGNAL RECEIVED: CaseState", instance)
    if not instance.case.case_url or instance.set_in_open_zaak or instance.system_build:
        print("=> SIGNAL PASS")
    elif instance.status == CaseState.CaseStateChoice.HANDHAVING:
        print("=> SIGNAL HANDHAVING")
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
            create_open_zaak_case(
                instance.case,
                zaaktype_identificatie=settings.OPENZAAK_ZAAKTYPE_IDENTIFICATIE_HANDHAVEN,
            )
        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)
    elif instance.status == CaseState.CaseStateChoice.AFGESLOTEN:
        print("=> SIGNAL AFGESLOTEN")
        try:
            previous_casestate = CaseState.objects.get(
                case=instance.case, status=CaseState.CaseStateChoice.HANDHAVING
            )
            print("=> Afsluiten zaak in Handhaven")
            # Case has status Handhaven so set Resultaat "Handhaven uitgevoerd"
            create_open_zaak_case_resultaat(instance.case)
            # Set Status "Afsluiten" to close the case in open-zaak
            create_open_zaak_case_status(instance)
            # Update previous CaseState
            previous_casestate.set_in_open_zaak = True
            previous_casestate.save()
            # Update current instance of CaseState
            instance.set_in_open_zaak = True
            instance.save()
        except CaseState.DoesNotExist:
            print("=> Afsluiten zaak in Toezicht")
            # Case has status Toezicht so set Resultaat "Toezicht afgebroken"
            create_open_zaak_case_resultaat(
                instance.case,
                omschrijving_generiek=settings.OPENZAAK_RESULTAATTYPE_OMSCHRIJVING_GENERIEK_AFGEBROKEN,
            )
            # Set Status "Afsluiten" to close the case in open-zaak
            create_open_zaak_case_status(instance)
            # Get previous CaseState
            previous_casestate = CaseState.objects.get(
                case=instance.case, status=CaseState.CaseStateChoice.TOEZICHT
            )
            # Update previous CaseState
            previous_casestate.set_in_open_zaak = True
            previous_casestate.save()
            # Update current instance of CaseState
            instance.set_in_open_zaak = True
            instance.save()
        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)
    else:
        print("=> SIGNAL ELSE")


@receiver(post_save, sender=CaseDocument)
def create_case_document_instance_in_openzaak(sender, instance, created, **kwargs):
    if created:
        try:
            connect_case_and_document(instance)
        except ClientError as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)
