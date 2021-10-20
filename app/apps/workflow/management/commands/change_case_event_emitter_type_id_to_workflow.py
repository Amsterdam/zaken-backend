import logging

from django.apps import apps
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        CaseEvent = apps.get_model("events", "CaseEvent")
        ContentType = apps.get_model(app_label="contenttypes", model_name="ContentType")

        old_generic_completed_task_contenttype = ContentType.objects.filter(
            app_label="camunda", model="genericcompletedtask"
        ).first()
        new_generic_completed_task_contenttype = ContentType.objects.filter(
            app_label="workflow", model="genericcompletedtask"
        ).first()

        print(old_generic_completed_task_contenttype)
        print(new_generic_completed_task_contenttype)

        if (
            old_generic_completed_task_contenttype
            and new_generic_completed_task_contenttype
        ):
            case_events = CaseEvent.objects.filter(
                emitter_type_id=old_generic_completed_task_contenttype.id
            )
            print(case_events)
            case_events.update(
                emitter_type_id=new_generic_completed_task_contenttype.id
            )
