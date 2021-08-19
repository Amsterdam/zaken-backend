import logging

logger = logging.getLogger(__name__)


# @receiver(
#     post_save,
#     sender=GenericCompletedTask,
#     dispatch_uid="generic_completed_init_in_camunda",
# )
# def create_generic_completed_instance_in_camunda(sender, instance, created, **kwargs):
#     if created:
#         CamundaService().complete_task(instance.camunda_task_id, instance.variables)
