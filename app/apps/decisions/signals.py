from apps.decisions.models import Decision
from apps.summons.models import Summon
from apps.workflow.models import CaseWorkflow
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Decision, dispatch_uid="decision_complete_camunda_task")
def update_decision_with_summon(sender, instance, created, **kwargs):
    """
    TODO: Temporary hook to update decision with a summon instance.
    This will be resolved when we support multiple summons.
    """
    if created:
        task = CaseWorkflow.get_task_by_task_id(instance.case_user_task_id)
        task.workflow.complete_user_task_and_create_new_user_tasks(
            task.task_id,
            {
                "type_besluit": {"value": instance.decision_type.camunda_option},
            },
        )
        summon = Summon.objects.filter(
            id=task.workflow.get_data().get("summon_id", {}).get("value", 0)
        ).first()
        if summon:
            instance.summon = summon
            instance.save()

        # task_variables = CamundaService().get_task_variables(instance.case_user_task_id)
        # if task_variables:
        #     summon_id = task_variables.get("summon_id", {}).get("value", 0)
        #     summon = Summon.objects.filter(id=summon_id).first()
        #     if summon:
        #         instance.summon = summon
        #         instance.save()

        # CamundaService().complete_task(
        #     instance.case_user_task_id,
        #     {"type_besluit": {"value": instance.decision_type.camunda_option}},
        # )
