import logging

from apps.visits.models import Visit
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        uncompleted_visits = (
            Visit.objects.filter(
                completed=False,
            )
            .distinct("case_user_task_id")
            .order_by("case_user_task_id", "-start_time")
        )
        print("command: unique_user_task_ids")
        print("visits")
        print(uncompleted_visits.count())
        print(uncompleted_visits)
        for v in uncompleted_visits:
            v.completed = True
            v.save()
