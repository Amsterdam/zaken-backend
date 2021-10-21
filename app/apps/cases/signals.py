import logging

from apps.cases.models import CaseClose, CitizenReport
from apps.workflow.models import CaseWorkflow
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CitizenReport, dispatch_uid="complete_citizen_report_task")
def complete_citizen_report_task(sender, instance, created, **kwargs):
    if instance.case_user_task_id != "-1" and created:
        CaseWorkflow.complete_user_task(instance.case_user_task_id, {})


@receiver(post_save, sender=CaseClose)
def close_case(sender, instance, created, **kwargs):
    if instance.case_user_task_id != "-1" and created:
        CaseWorkflow.complete_user_task(instance.case_user_task_id, {})
        instance.case.close_case()
