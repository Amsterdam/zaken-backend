import logging
from datetime import datetime

from api.config import (
    Action,
    CloseReason,
    DaySegment,
    DecisionType,
    NextStep,
    Objection,
    Priority,
    ReviewRequest,
    Situations,
    SummonTypes,
    Violation,
    WeekSegment,
)
from api.mock import get_person

logger = logging.getLogger("api")


class Task:
    """
    Map Spiff task_name to legacy-Camunda task_name
    """

    check_decision = (
        "task_check_concept_decision",
        "Activity_1j6vc31",
    )  # Nakijken besluit
    check_incoming_view = (
        "task_check_incoming_point_of_view",
        "Activity_1nylgs7",
    )  # Controleren binnenkomst zienswijze
    check_notices = (
        "task_check_summons",
        "Activity_0xocoed",
    )  # Nakijken aanschrijving(en)
    close_case = ("task_close_case", "task_close_case")
    contact_district = (
        "task_contact_city_district",
        "Activity_1tl73nx",
    )  # Contacteren stadsdeel
    contact_owner = (
        "task_contact_owner",
        "Activity_0gjczg7",
    )  # Contacteren eigenaar
    create_concept_notices = (
        "task_create_concept_summons",
        "Activity_15hr2wx",
    )  # Opstellen concept aanschrijvingen
    create_concept_decision = (
        "task_make_concept_decision",
        "Activity_08cj18o",
    )  # Opstellen concept besluit

    create_findings_report = (
        "task_create_report_of_findings",
        "task_rapport_van_bevindingen_opstellen",
    )  # Opstellen rapport van bevindingen
    create_home_visit_report = (
        "task_prepare_abbreviated_visit_rapport",
        "Activity_02t4qsu",
    )  # Opstellen verkorte rapportage huisbezoek
    create_picture_report = (
        "task_create_picture_rapport",
        "task_beeldverslag_opstellen",
    )  # Opstellen beeldverslag
    feedback_reporters = (
        "task_feedback_reporter",
        "Activity_0bc2n3t",
    )  # Terugkoppelen melder(s)
    judge_reopening_request = (
        "task_judge_reopening_request",
        "Activity_0fp5tdz",
    )  # Beoordelen heropeningsverzoek
    judge_view = (
        "task_judge_point_of_view",
        "Activity_18ear0d",
    )  # Beoordelen zienswijze
    monitor_incoming_permit_request = (
        "task_monitor_incoming_permit_application",
        "Activity_1mkl5rk",
    )  # Monitoren binnenkomen vergunningaanvraag
    monitor_incoming_view = (
        "task_monitor_incoming_point_of_view",
        "Activity_13ccsra",
    )  # Monitoren binnenkomen zienswijze
    monitor_incoming_warrant = (
        "task_monitor_incoming_authorization",
        "Activity_1lv323s",
    )  # Monitoren binnenkomen machtiging
    monitor_reopening_request = (
        "task_monitor_reopening_request",
        "Activity_0wienly",
    )  # Monitoren heropeningsverzoek
    monitor_reopening_request_to_be_delivered = (
        "task_monitor_new_reopening_request",
        "Activity_0zh0d0s",
    )  # Monitoren nieuw aan te leveren heropeningsverzoek
    plan_next_step = (
        "task_set_next_step",
        "Activity_0id7dcf",
    )  # Uitzetten vervolgstap
    reopen = (
        "task_reopening",
        "Activity_1fovs3d",
    )  # Heropenen
    request_warrant = (
        "task_request_authorization",
        "Activity_03lt0e7",
    )  # Aanvragen machtiging
    save_fire_brigade_advice = (
        "task_save_fireman_advice",
        "Activity_19r9rzm",
    )  # Opslaan brandweeradvies
    schedule_recheck = (
        "task_schedule_recheck",
        "Activity_1tmqvpn",
    )  # Uitzetten hercontrole
    send_tax_collection = (
        "task_send_tax_collection",
        "Activity_14kdv7u",
    )  # Versturen invordering belastingen

    # non-generic-tasks
    debrief = ("task_create_debrief", "task_create_debrief")
    decision = ("task_create_decision", "task_create_decision")
    schedule = ("task_create_schedule", "task_create_schedule")
    summon = (
        "task_create_summon",
        "task_create_summon",
    )  # Verwerk aanschrijving
    visited = ("task_create_visit", "task_create_visit")  # Doorgeven ${status_name} TOP


class AbstractUserTask:
    data = None

    def __init__(self, **data):
        self.data = data

    def run(self, api, case):
        task_name = api.get_task_name(self.task)
        open_tasks = api.get_case_tasks(case["id"])
        tasks = list(task for task in open_tasks if task["task_name_id"] == task_name)

        if len(tasks) == 0:
            raise Exception(f"No open task found. Cant find task_name_id = {task_name}")
        elif len(tasks) > 1:
            raise Exception("More then one task found")

        extra = self.get_post_data(case, tasks[0])
        post_data = self.data | extra if self.data else extra
        api.call("post", f"/{self.endpoint}/", post_data)

    def get_post_data(self, case, task):
        raise NotImplementedError


class Visit(AbstractUserTask):
    endpoint = "visits"
    task = Task.visited

    def __init__(
        self,
        authors=[],
        start_time=None,
        situation=Situations.ACCESS_GRANTED,
        can_next_visit_go_ahead=False,
    ):
        super(Visit, self).__init__(
            authors=authors,
            start_time=start_time if start_time else str(datetime.now()),
            situation=situation,
            can_next_visit_go_ahead=can_next_visit_go_ahead,
        )

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
            "task": task["camunda_task_id"],
        }


class ScheduleVisit(AbstractUserTask):
    endpoint = "schedules"
    task = Task.schedule

    def __init__(
        self,
        action=Action.HOUSE_VISIT,
        week_segment=WeekSegment.WEEKDAY,
        day_segment=DaySegment.DAYTIME,
        priority=Priority.HIGH,
    ):
        super(ScheduleVisit, self).__init__(
            action=action,
            week_segment=week_segment,
            day_segment=day_segment,
            priority=priority,
        )

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
            "camunda_task_id": task["camunda_task_id"],
        }


class Debrief(AbstractUserTask):
    endpoint = "debriefings"
    task = Task.debrief

    def __init__(self, violation=Violation.NO, feedback="Some feedback"):
        super(Debrief, self).__init__(violation=violation, feedback=feedback)

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
            "camunda_task_id": task["camunda_task_id"],
        }


class Close(AbstractUserTask):
    endpoint = "case-close"
    task = Task.close_case

    def __init__(
        self, reason=CloseReason.HolidayRental.NO_FROUD, description="Some description"
    ):
        super(Close, self).__init__(reason=reason, description=description)

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
            "theme": case["theme"],
            "camunda_task_id": task["camunda_task_id"],
        }


class AssertNextOpenTasks:
    def __init__(self, tasks: list[str]):
        self.tasks = filter(lambda task: task is not None, tasks)

    def run(self, api, case):
        # Get the task names we want to check
        assert_names = list(map(api.get_task_name, self.tasks))
        assert_names.sort()

        # Get the names of all open tasks
        open_tasks = api.get_case_tasks(case["id"])
        open_task_names = list(map(lambda task: task["task_name_id"], open_tasks))
        open_task_names.sort()

        logger.info(f"Expecting {assert_names} == {open_task_names}")
        if assert_names != open_task_names:
            raise Exception(
                f"Expected {assert_names}, found {open_task_names}. Case id:{case['id']}"
            )


class AssertNumberOfOpenTasks:
    def __init__(self, count):
        self.count = count

    def run(self, api, case):
        num_open_tasks = len(api.get_case_tasks(case["id"]))
        if num_open_tasks != self.count:
            raise Exception(
                f"{self.count} open tasks expected, found {num_open_tasks}. Case id:{case['id']}"
            )


class GenericUserTask(AbstractUserTask):
    endpoint = "camunda/task/complete"

    def __init__(self, **variables):
        self.variables = variables
        super(GenericUserTask, self).__init__()

    def get_post_data(self, case, task):
        return {
            "variables": self.variables,
            "camunda_task_id": task["camunda_task_id"],
            "case": case["id"],
        }


class PlanNextStep(GenericUserTask):
    task = Task.plan_next_step

    def __init__(self, next_step=NextStep.CLOSE):
        data = {"next_step": {"value": next_step}}

        super(PlanNextStep, self).__init__(**data)


class CheckNotices(GenericUserTask):
    task = Task.check_notices


class FeedbackReporters(GenericUserTask):
    task = Task.feedback_reporters


class HomeVisitReport(GenericUserTask):
    task = Task.create_home_visit_report


class CreatePictureReport(GenericUserTask):
    task = Task.create_picture_report


class CreateFindingsReport(GenericUserTask):
    task = Task.create_findings_report


class CreateConceptNotices(GenericUserTask):
    task = Task.create_concept_notices


class ContactOwner(GenericUserTask):
    task = Task.contact_owner


class JudgeReopeningRequest(GenericUserTask):
    task = Task.judge_reopening_request

    def __init__(self, review_request=ReviewRequest.ACCEPTED):
        data = {"beoordeling_verzoek": {"value": review_request}}

        super(JudgeReopeningRequest, self).__init__(**data)


class MonitorReopeningRequest(GenericUserTask):
    task = Task.monitor_reopening_request
    # heropeningsverzoek_binnengekomen


class MonitorReopeningRequestToBeDelivered(GenericUserTask):
    task = Task.monitor_reopening_request_to_be_delivered


class Reopen(GenericUserTask):
    task = Task.reopen


class ScheduleRecheck(GenericUserTask):
    task = Task.schedule_recheck


class SaveFireBrigadeAdvice(GenericUserTask):
    task = Task.save_fire_brigade_advice


class MonitorIncomingView(GenericUserTask):
    task = Task.monitor_incoming_view

    def __init__(self, objection=False):
        data = {"is_civilian_objection_received": {"value": objection}}

        super(MonitorIncomingView, self).__init__(**data)


class JudgeView(GenericUserTask):
    task = Task.judge_view

    def __init__(self, objection_valid=True):
        data = {"is_citizen_objection_valid": {"value": objection_valid}}

        super(JudgeView, self).__init__(**data)


class CheckIncomingView(GenericUserTask):
    task = Task.check_incoming_view

    def __init__(self, objection=Objection.NO):
        data = {"is_civilian_objection_received": {"value": objection}}

        super(CheckIncomingView, self).__init__(**data)


class CreateConceptDecision(GenericUserTask):
    task = Task.create_concept_decision


class CheckDecision(GenericUserTask):
    task = Task.check_decision


class SendTaxCollection(GenericUserTask):
    task = Task.send_tax_collection


class ContactDistrict(GenericUserTask):
    task = Task.contact_district


class Decision(AbstractUserTask):
    endpoint = "decisions"
    task = Task.decision

    def __init__(self, type=DecisionType.HolidayRental.NO_DECISION):
        data = {"decision_type": type}
        super(Decision, self).__init__(**data)

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
            "camunda_task_id": task["camunda_task_id"],
        }


class Summon(AbstractUserTask):
    endpoint = "summons"
    task = Task.summon

    def __init__(
        self,
        type=SummonTypes.HolidayRental.LEGALIZATION_LETTER,
        persons=None,
    ):
        super(Summon, self).__init__(
            type=type,
            persons=persons if persons else [get_person()],
        )

    def get_post_data(self, case, task):
        return {
            "case": case["id"],
            "camunda_task_id": task["camunda_task_id"],
        }
