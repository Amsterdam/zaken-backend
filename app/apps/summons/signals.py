import logging
import sys

from apps.camunda.services import CamundaService
from apps.summons.models import Summon
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Summon, dispatch_uid="summon_init_in_camunda")
def create_summon_instance_in_camunda(sender, instance, created, **kwargs):
    if created:
        # TODO: create belastingdienst number
        if instance.case.summons.count() == 1:
            instance.summon = instance.case.summons.all()[0]
            instance.save()

    task = False
    for camunda_id in instance.case.camunda_ids:
        task = CamundaService().get_task_by_task_name_id_and_camunda_id(
            "task_create_summon", camunda_id
        )
        if task:
            break

    if task:
        CamundaService().complete_task(
            task["id"],
            {
                "type_aanschrijving": {"value": instance.type.camunda_option},
                "names": {
                    "value": ", ".join(
                        [person.__str__() for person in instance.persons.all()]
                    )
                },
            },
        )
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

    # if created and "test" not in sys.argv:
    #     (camunda_id, _) = CamundaService().start_instance(
    #         case_identification=instance.case.identification,
    #         process="zaak_wonen_summon",
    #         request_body=json.dumps(
    #             {
    #                 "variables": {
    #                     "names": {
    #                         "value": ", ".join(
    #                             [person.__str__() for person in instance.persons.all()]
    #                         ),
    #                         "type": "String",
    #                     },
    #                     "type_aanschrijving": {
    #                         "value": instance.type.camunda_option,
    #                         "type": "String",
    #                     },
    #                     "sluitingsbesluit": {
    #                         "value": False,
    #                         "type": "Boolean",
    #                     },
    #                     "case_identification": {
    #                         "value": instance.case.identification,
    #                         "type": "String",
    #                     },
    #                     "zaken_access_token": {
    #                         "value": settings.CAMUNDA_SECRET_KEY,
    #                         "type": "String",
    #                     },
    #                     "zaken_state_endpoint": {
    #                         "value": f'{settings.ZAKEN_CONTAINER_HOST}{reverse("camunda-workers-state")}',
    #                         "type": "String",
    #                     },
    #                     "zaken_end_state_endpoint": {
    #                         "value": f'{settings.ZAKEN_CONTAINER_HOST}{reverse("camunda-workers-end-state")}',
    #                         "type": "String",
    #                     },
    #                     "endpoint": {
    #                         "value": settings.ZAKEN_CONTAINER_HOST,
    #                         "type": "String",
    #                     },
    #                 }
    #             }
    #         ),
    #     )
    #     case = instance.case
    #     case = case.add_camunda_id(camunda_id)
    #     case.save()


@receiver(post_save, sender=Summon)
def create_summon_instance_in_openzaak(sender, instance, created, **kwargs):
    if created and "test" not in sys.argv:
        pass  # pass for now
