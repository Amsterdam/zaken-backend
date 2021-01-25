from apps.camunda.services import CamundaService
from apps.cases.models import Case
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver


@receiver(post_save, sender=Case, dispatch_uid="case_init_in_camunda")
def create_case_instance_in_camunda(sender, instance, created, **kwargs):
    if created:
        camunda_id = CamundaService().start_instance()
        instance.camunda_id = camunda_id
        instance.save()


@receiver(post_save, sender=Case)
def create_case_instance_in_openzaak(sender, instance, created, **kwargs):
    if created:
        # TODO: Add code when OpenZaak connection is ready
        pass
