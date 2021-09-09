from apps.workflow.models import Workflow
from config.celery import app as celery_app

DEFAULT_RETRY_DELAY = 10


@celery_app.task(bind=True)
def update_workflows(self):
    for workflows in Workflow.objects.all():
        workflows.update_workflow()
    return "Update workflows complete"
