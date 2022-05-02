import logging

from apps.visits.models import Visit
from apps.workflow.models import CaseUserTask
from django.core.management.base import BaseCommand
from django.db.models import OuterRef, Subquery

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):

        last_tasks = CaseUserTask.objects.filter(
            id=OuterRef("case_user_task_id"),
            task_name="task_create_visit",
            completed=False,
        ).order_by("-created")
        uncompleted_visits = (
            Visit.objects.exclude(case_user_task_id="-1")
            .annotate(last_task=Subquery(last_tasks.values("task_name")))
            .filter(last_task__isnull=False)
        )

        # uncompleted_visits = (
        #     Visit.objects.filter(
        #         # completed=False,
        #         case__tasks__task_name="task_create_visit",
        #         case__tasks__completed=False,
        #     )
        #     .exclude(case_user_task_id="-1")
        #     .distinct("case_user_task_id")
        #     .order_by("case_user_task_id", "-start_time")
        # )

        print("command: unique_user_task_ids")
        print("visits")
        print(uncompleted_visits.count())
        print(uncompleted_visits)
        # for v in uncompleted_visits:
        # v.completed = True
        # v.save()
