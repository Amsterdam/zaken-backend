import datetime

from apps.workflow.models import DEFAULT_USER_TASK_DUE_DATE, USER_TASKS, CaseUserTask
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=CaseUserTask, dispatch_uid="case_user_task_pre_save")
def case_user_task_pre_save(sender, instance, **kwargs):
    if not instance.id:
        instance.due_date = datetime.datetime.now() + USER_TASKS.get(
            instance.task_name, {}
        ).get("due_date", DEFAULT_USER_TASK_DUE_DATE)
