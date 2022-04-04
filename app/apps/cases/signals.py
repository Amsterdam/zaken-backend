import logging

from apps.cases.models import Case, CaseClose, CaseState, CitizenReport
from apps.cases.tasks import task_close_case
from apps.workflow.models import CaseWorkflow
from apps.workflow.tasks import task_create_citizen_report_worflow_for_case
from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Case, dispatch_uid="case_pre_save")
def case_pre_save(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return
    if not instance.id:
        instance.sensitive = instance.theme.sensitive


@receiver(post_save, sender=Case, dispatch_uid="start_workflow_for_case")
def start_workflow_for_case(sender, instance, created, **kwargs):
    from apps.workflow.tasks import task_create_main_worflow_for_case

    if kwargs.get("raw"):
        return
    data = {}
    if created:
        CaseState.objects.get_or_create(case=instance)

        cached_legacy_bwv_case_key = (
            f"legacy_bwv_case_id_{instance.legacy_bwv_case_id}_create_data"
        )
        cached_legacy_bwv_case = cache.get(cached_legacy_bwv_case_key, {})
        data.update(cached_legacy_bwv_case)
        task_create_main_worflow_for_case.delay(case_id=instance.id, data=data)


@receiver(post_save, sender=CitizenReport, dispatch_uid="complete_citizen_report_task")
def complete_citizen_report_task(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if instance.case_user_task_id != "-1" and created:
        CaseWorkflow.complete_user_task(instance.case_user_task_id, {})
    if created:
        task_create_citizen_report_worflow_for_case.delay(instance.id)


@receiver(post_save, sender=CaseClose)
def close_case(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if instance.case_user_task_id != "-1" and created:
        CaseState.objects.get_or_create(
            case=instance.case,
            status=CaseState.CaseStateChoice.AFGESLOTEN,
        )
        CaseWorkflow.complete_user_task(instance.case_user_task_id, {})
        task_close_case.delay(instance.case.id)
