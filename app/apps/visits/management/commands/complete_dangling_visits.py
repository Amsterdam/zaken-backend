import logging

from apps.visits.models import Visit
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        uncompleted_visits = (
            Visit.objects.filter(
                case__tasks__task_name="task_create_visit",
                case__tasks__completed=False,
            )
            .exclude(case_user_task_id="-1")
            .distinct("case_user_task_id")
            .order_by("case_user_task_id", "-start_time")
        )
        for v in uncompleted_visits:
            task = v.case.tasks.filter(
                task_name="task_create_visit",
                completed=False,
                id=int(v.case_user_task_id),
            )
            if task:
                v.completed = True
                v.save()
