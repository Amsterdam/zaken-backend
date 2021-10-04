import logging

from apps.cases.models import Case
from apps.workflow.tasks import task_start_workflow_for_existing_case
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        cases = Case.objects.filter(workflows__isnull=True)

        for case in cases:
            task_start_workflow_for_existing_case.delay(case.id)

        logger.info(cases)
