from config.celery import app as celery_app

DEFAULT_RETRY_DELAY = 10


@celery_app.task(bind=True)
def update_workflows(self):
    from apps.workflow.models import CaseWorkflow

    for workflows in CaseWorkflow.objects.all():
        workflows.update_workflow()
    return "Update workflows complete"


@celery_app.task(bind=True)
def accept_message_for_workflow(self, workflow_id, message, extra_data):
    from apps.workflow.models import CaseWorkflow

    workflow = CaseWorkflow.objects.filter(id=workflow_id).first()
    if not workflow:
        return "workflow not found: %s" % workflow_id

    workflow.accept_message(message, extra_data)

    return "workflow: %s, message: %s" % (
        workflow_id,
        message,
    )
