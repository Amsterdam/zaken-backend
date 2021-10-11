import datetime

from apps.workflow.models import DEFAULT_USER_TASK_DUE_DATE, USER_TASKS, CaseUserTask
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=CaseUserTask, dispatch_uid="case_user_task_pre_save")
def case_user_task_pre_save(sender, instance, **kwargs):
    if not instance.id:
        now = datetime.datetime.now()
        d = datetime.datetime(year=now.year, month=now.month, day=now.day)
        instance.due_date = d + USER_TASKS.get(instance.task_name, {}).get(
            "due_date", DEFAULT_USER_TASK_DUE_DATE
        )
