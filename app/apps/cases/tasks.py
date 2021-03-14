from apps.camunda.services import CamundaService
from apps.cases.models import Case
from config.celery import app as celery_app


@celery_app.task(bind=True)
def start_camunda_instance(self, identification, request_body):
    (camunda_id, response) = CamundaService().start_instance(
        case_identification=identification, request_body=request_body
    )
    if camunda_id:
        case = Case.objects.get(identification=identification)
        case.camunda_id = camunda_id
        case.save()
