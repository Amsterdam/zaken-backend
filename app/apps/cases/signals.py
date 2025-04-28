import logging

from apps.cases.models import Case, CaseState
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Case, dispatch_uid="case_pre_save")
def case_pre_save(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return
    if not instance.id:
        instance.sensitive = instance.theme.sensitive
        instance.is_enforcement_request = bool(
            instance.reason.snake_case_name == "handhavingsverzoek"
        )


@receiver(post_save, sender=Case, dispatch_uid="start_workflow_for_case")
def start_workflow_for_case(sender, instance, created, **kwargs):
    from apps.workflow.tasks import task_create_main_worflow_for_case

    if kwargs.get("raw"):
        return
    data = {}
    if created:
        CaseState.objects.get_or_create(case=instance)
        task_create_main_worflow_for_case.delay(case_id=instance.id, data=data)
