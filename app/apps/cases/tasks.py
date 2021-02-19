from apps.camunda.services import CamundaService
from apps.cases.models import Case
from config.celery import app as celery_app


@celery_app.task(bind=True)
def start_camunda_instance(self, identification):
    camunda_id = CamundaService().start_instance(case_identification=identification)
    case = Case.objects.get(identification=identification)
    case.camunda_id = camunda_id
    case.save()
