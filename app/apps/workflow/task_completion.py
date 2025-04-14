import copy
import logging

from apps.workflow.models import CaseUserTask, CaseWorkflow, GenericCompletedTask
from apps.workflow.user_tasks import get_task_by_name
from django.db import transaction

logger = logging.getLogger(__name__)


def complete_user_task(data):
    try:
        with transaction.atomic():
            completed_task = GenericCompletedTask.objects.create(**data)
            task = CaseUserTask.objects.filter(
                id=completed_task.case_user_task_id
            ).first()
            if task:
                data = copy.deepcopy(completed_task.variables)
                data.pop("mapped_form_data")
                user_task_type = get_task_by_name(task.task_name)
                user_task_instance = user_task_type(task)
                data.update(user_task_instance.get_data())
                CaseWorkflow.complete_user_task(task.id, data, wait=True, timeout=15)
                return f"CaseUserTask {completed_task.case_user_task_id} has been completed"
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        raise e
