import celery
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core import management

logger = get_task_logger(__name__)

DEFAULT_RETRY_DELAY = 2
MAX_RETRIES = 6

LOCK_EXPIRE = 5


class BaseTaskWithRetry(celery.Task):
    autoretry_for = (Exception,)
    max_retries = MAX_RETRIES
    default_retry_delay = DEFAULT_RETRY_DELAY


@shared_task(bind=True, base=BaseTaskWithRetry)
def task_complete_dangling_visits(self):
    management.call_command("complete_dangling_visits", verbosity=0)
    return "task_complete_dangling_visits"
