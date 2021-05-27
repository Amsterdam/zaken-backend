from apps.camunda.services import CamundaService
from apps.cases.models import Case, CaseProcessInstance
from config.celery import app as celery_app
from django.conf import settings


@celery_app.task(bind=True)
def start_camunda_instance(self, identification, request_body):
    case = Case.objects.get(id=identification)
    case_process_instance = CaseProcessInstance.objects.create(case=case)
    case_process_instance.save()

    request_body["variables"]["case_process_id"] = {
        "value": case_process_instance.process_id.__str__()
    }

    (camunda_id, response) = CamundaService().start_instance(
        case_identification=str(identification), request_body=request_body
    )

    if camunda_id:
        case_process_instance.camunda_process_id = camunda_id
        case = case.add_camunda_id(camunda_id)
        case.save()
        case_process_instance.save()


@celery_app.task(bind=True)
def create_mock_schedule(self, case_id):
    import time

    from apps.camunda.services import CamundaService
    from apps.schedules.models import (
        Action,
        DaySegment,
        Priority,
        Schedule,
        WeekSegment,
    )

    case = Case.objects.get(id=case_id)

    def get_schedule_task(case):
        task = CamundaService().get_task_by_task_name_id_and_camunda_id(
            "task_create_schedule", case.camunda_id
        )
        return task

    print("Waiting to create schedule...")
    count = 0
    while not get_schedule_task(case):
        time.sleep(2)
        count += 1
        if count > 30:
            print("Giving up")
            return

    print("Ready to make a schedule")
    action = Action.objects.get(name=settings.DEFAULT_SCHEDULE_ACTIONS[0])
    week_segment = WeekSegment.objects.get(
        name=settings.DEFAULT_SCHEDULE_WEEK_SEGMENTS[0]
    )
    day_segment = DaySegment.objects.get(name=settings.DEFAULT_SCHEDULE_DAY_SEGMENTS[0])
    priority = Priority.objects.get(name=settings.DEFAULT_SCHEDULE_NORMAL_PRIORITY)

    Schedule.objects.create(
        case=case,
        action=action,
        week_segment=week_segment,
        day_segment=day_segment,
        priority=priority,
    )
