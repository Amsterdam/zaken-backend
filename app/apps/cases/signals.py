import logging

from apps.cases.models import Case, CaseClose, CitizenReport
from apps.cases.tasks import task_close_case
from apps.workflow.models import CaseWorkflow
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
    if hasattr(instance, "status_name"):
        data.update({"status_name": getattr(instance, "status_name")})
    if created:
        task_create_main_worflow_for_case.delay(case_id=instance.id, data=data)


@receiver(post_save, sender=CitizenReport, dispatch_uid="complete_citizen_report_task")
def complete_citizen_report_task(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if instance.case_user_task_id != "-1" and created:
        CaseWorkflow.complete_user_task(instance.case_user_task_id, {})


@receiver(post_save, sender=CaseClose)
def close_case(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return
    if instance.case_user_task_id != "-1" and created:
        CaseWorkflow.complete_user_task(instance.case_user_task_id, {})
        task_close_case.delay(instance.case.id)
