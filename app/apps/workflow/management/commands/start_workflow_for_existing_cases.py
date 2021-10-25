import logging

from apps.cases.models import Case
from apps.workflow.tasks import task_create_main_worflow_for_case
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        cases = Case.objects.filter(workflows__isnull=True)

        for case in cases:
            task_create_main_worflow_for_case.delay(case.id)

        logger.info(cases)
