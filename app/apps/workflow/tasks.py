import time

from config.celery import app as celery_app

DEFAULT_RETRY_DELAY = 10


@celery_app.task(bind=True)
def update_workflows(self):
    from apps.workflow.models import Workflow

    for workflows in Workflow.objects.all():
        workflows.update_workflow()
    return "Update workflows complete"


@celery_app.task(bind=True)
def send_message_to_workflow(self, workflow_id, message):
    from apps.workflow.models import Workflow

    workflow = Workflow.objects.filter(id=workflow_id).first()
    if not workflow:
        return "workflow not found: %s" % workflow_id
    time.sleep(100)
    workflow.accept_message(message)

    return "workflow: %s, message: %s" % (
        workflow_id,
        message,
    )
