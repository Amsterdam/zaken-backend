import logging

import celery
from celery import shared_task

DEFAULT_RETRY_DELAY = 2
logger = logging.getLogger(__name__)


class BaseTaskWithRetry(celery.Task):
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = DEFAULT_RETRY_DELAY


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_close_case(self, case_id):
    from apps.cases.models import Case

    case = Case.objects.get(id=case_id)
    case.close_case()

    return f"task_close_case: case with id '{case_id}' complete"
