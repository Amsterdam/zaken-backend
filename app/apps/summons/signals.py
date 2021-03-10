import json
import logging
import sys

from apps.camunda.services import CamundaService
from apps.summons.models import Summon
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Summon, dispatch_uid="summon_init_in_camunda")
def create_summon_instance_in_camunda(sender, instance, created, **kwargs):
    # CamundaService().send_message(
    #     "model_create_summon",
    #     json.dumps(
    #         {
    #             "names": {
    #                 "value": ", ".join(
    #                     [person.__str__() for person in instance.persons.all()]
    #                 )
    #             },
    #             "type_aanschrijving": {
    #                 "value": instance.type.camunda_option,
    #             },
    #             "sluitingsbesluit": {
    #                 "value": instance.intention_closing_decision,
    #             },
    #         }
    #     ),
    # )
    if created and "test" not in sys.argv:
        camunda_id = CamundaService().start_instance(
            case_identification=instance.case.identification,
            process="model_create_summon",
            request_body=json.dumps(
                {
                    "variables": {
                        "names": {
                            "value": ", ".join(
                                [person.__str__() for person in instance.persons.all()]
                            )
                        },
                        "type_aanschrijving": {
                            "value": instance.type.camunda_option,
                        },
                        "sluitingsbesluit": {
                            "value": instance.intention_closing_decision,
                        },
                    }
                }
            ),
        )
        case = instance.case
        case.camunda_id = camunda_id
        case.save()


@receiver(post_save, sender=Summon)
def create_summon_instance_in_openzaak(sender, instance, created, **kwargs):
    if created and "test" not in sys.argv:
        pass  # pass for now
