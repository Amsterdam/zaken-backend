import json
import logging
from datetime import datetime

from api import events
from api.case import Case
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
from api.util import WaitForTimer

logger = logging.getLogger("api")


class AbstractUserTask:
    data = None
    event = None

    def __init__(self, **data):
        self.data = data

    def is_async(self):
        return hasattr(self, "asynchronous") and self.asynchronous

    def run(self, client, case: Case):
        open_tasks = client.get_case_tasks(case.data["id"])
        tasks = list(
            task for task in open_tasks if task["task_name_id"] == self.task_name
        )

        if len(tasks) == 0:
            raise Exception(
                f"No open task found. Cant find task_name_id = '{self.task_name}' ({self.description}) for case {case}"
            )
        elif len(tasks) > 1:
            raise Exception("More then one task found")

        extra = self.get_post_data(case, tasks[0])
        post_data = self.data | extra if self.data else extra
        client.call("post", f"/{self.endpoint}/", post_data)

        # Store expected events in the eventlog
        if self.event:
            case.timeline.append(self.event)

        events = client.get_case_events(case.data["id"])

        logging.info(f"Finding events for case id {case.data['id']} ...")
        logging.info(f"Expect: {case.timeline}, found:")
        logging.info(f"{json.dumps(events, sort_keys=True, indent=4)}\n\n")

        for index, event_class in enumerate(case.timeline):
            print(f"compare '{event_class.type}' with '{events[index]['type']}'")
            if event_class.type != events[index]["type"]:
                raise Exception("Timeline issue")

    def get_post_data(self, case, task):
        raise NotImplementedError


class GenericUserTask(AbstractUserTask):
    endpoint = "camunda/task/complete"
    event = events.GenericTaskEvent

    def __init__(self, **variables):
        self.variables = variables
        super(GenericUserTask, self).__init__()

    def get_post_data(self, case, task):
        return {
            "variables": self.variables,
            "case": case.data["id"],
            "task": task["case_user_task_id"],
        }


class FeedbackReporters(GenericUserTask):
    task_name = "task_feedback_reporter"
    description = "Terugkoppelen melder(s)"

    @staticmethod
    def get_steps():
        """
        Weird one, because it's dependent on timer. Also there is no
        preceiding step.
        """
        return [__class__()]


class ScheduleVisit(AbstractUserTask):
    asynchronous = True
    event = events.ScheduleEvent
    endpoint = "schedules"
    task_name = "task_create_schedule"
    description = "Inplannen $status_name"

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

    @staticmethod
    def get_steps():
        return [__class__()]

    def get_post_data(self, case, task):
        return {
            "case": case.data["id"],
            "case_user_task_id": task["case_user_task_id"],
        }


class Visit(AbstractUserTask):
    event = events.VisitEvent
    endpoint = "visits"
    task_name = "task_create_visit"
    description = "Doorgeven $status_name TOP"

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

    @staticmethod
    def get_steps(
        situation=Situations.ACCESS_GRANTED,
        can_next_visit_go_ahead=False,
    ):
        return [
            *ScheduleVisit.get_steps(),
            __class__(
                situation=situation, can_next_visit_go_ahead=can_next_visit_go_ahead
            ),
        ]

    def get_post_data(self, case, task):
        return {
            "case": case.data["id"],
            "task": task["camunda_task_id"],
        }


class Debrief(AbstractUserTask):
    event = events.DebriefingEvent
    endpoint = "debriefings"
    task_name = "task_create_debrief"
    description = "Verwerken debrief"

    def __init__(self, violation=Violation.NO, feedback="Some feedback"):
        super(Debrief, self).__init__(violation=violation, feedback=feedback)

    @staticmethod
    def get_steps(violation=Violation.NO):
        return [*Visit.get_steps(), __class__(violation=violation)]

    def get_post_data(self, case, task):
        return {
            "case": case.data["id"],
            "case_user_task_id": task["case_user_task_id"],
        }


class CreatePictureReport(GenericUserTask):
    task_name = "task_create_picture_rapport"
    description = "Opstellen beeldverslag"

    @staticmethod
    def get_steps():
        return [*Debrief.get_steps(violation=Violation.YES), __class__()]


class CreateFindingsReport(GenericUserTask):
    task_name = "task_create_report_of_findings"
    description = "Opstellen rapport van bevindingen"

    @staticmethod
    def get_steps():
        return [*Debrief.get_steps(violation=Violation.YES), __class__()]


class CreateConceptNotices(GenericUserTask):
    task_name = "task_create_concept_summons"
    description = "Opstellen concept aanschrijvingen"

    @staticmethod
    def get_steps():
        return [*Debrief.get_steps(violation=Violation.YES), __class__()]


class HomeVisitReport(GenericUserTask):
    task_name = "task_prepare_abbreviated_visit_rapport"
    description = "Opstellen verkorte rapportage huisbezoek"

    @staticmethod
    def get_steps(to_other_team=False):
        violation = Violation.SEND_TO_OTHER_THEME if to_other_team else Violation.NO
        return [
            *Debrief.get_steps(violation=violation),
            __class__(),
        ]


class CheckNotices(GenericUserTask):
    task_name = "task_check_summons"
    description = "Nakijken aanschrijving(en)"

    @staticmethod
    def get_steps():
        return [
            *Debrief.get_steps(violation=Violation.YES),
            CreatePictureReport(),
            CreateFindingsReport(),
            CreateConceptNotices(),
            __class__(),
        ]


class ProcessNotice(AbstractUserTask):
    asynchronous = True
    event = events.SummonEvent
    endpoint = "summons"
    task_name = "task_create_summon"
    description = "Verwerk aanschrijving"

    def __init__(
        self,
        type=SummonTypes.HolidayRental.LEGALIZATION_LETTER,
        persons=None,
    ):
        super(ProcessNotice, self).__init__(
            type=type,
            persons=persons if persons else [get_person()],
        )

    @staticmethod
    def get_steps(type=SummonTypes.HolidayRental.LEGALIZATION_LETTER):
        return [
            *CheckNotices.get_steps(),
            __class__(type=type),
        ]

    def get_post_data(self, case, task):
        return {
            "case": case.data["id"],
            "theme": case["theme"],
            "case_user_task_id": task["case_user_task_id"],
        }


class MonitorIncomingView(GenericUserTask):
    task_name = "task_monitor_incoming_point_of_view"
    description = "Monitoren binnenkomen zienswijze"

    def __init__(self, civilian_objection_received=True):
        # data = {"is_civilian_objection_received": {"value": objection}}

        super(MonitorIncomingView, self).__init__()

    @staticmethod
    def get_steps():
        return [
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.INTENTION_TO_FINE),
            __class__(),
        ]


class CheckIncomingView(GenericUserTask):
    task_name = "task_check_incoming_point_of_view"
    description = "Controleren binnenkomst zienswijze"

    def __init__(self, objection=Objection.NO):
        data = {"is_civilian_objection_received": {"value": objection}}

        super(CheckIncomingView, self).__init__(**data)

    @staticmethod
    def get_steps(objection=Objection.NO):
        return [
            *MonitorIncomingView.get_steps(),
            __class__(objection=objection),
        ]


class JudgeView(GenericUserTask):
    task_name = "task_judge_point_of_view"
    description = "Beoordelen zienswijze"

    def __init__(self, objection_valid=True):
        data = {"is_citizen_objection_valid": {"value": objection_valid}}

        super(JudgeView, self).__init__(**data)

    @staticmethod
    def get_steps(objection_valid=True):
        return [
            *MonitorIncomingView.get_steps(),
            __class__(objection_valid=objection_valid),
        ]


class MonitorIncomingPermitRequest(GenericUserTask):
    task_name = "task_monitor_incoming_permit_application"
    description = "Monitoren binnenkomen vergunningaanvraag"

    @staticmethod
    def get_steps(objection_valid=True):
        return [
            *CheckIncomingView.get_steps(),
            __class__(objection_valid=objection_valid),
        ]


class CreateConceptDecision(GenericUserTask):
    asynchronous = True
    task_name = "task_make_concept_decision"
    description = "Opstellen concept besluit"

    @staticmethod
    def get_steps():
        return [
            *JudgeView.get_steps(),
            __class__(),
        ]


class CheckConceptDecision(GenericUserTask):
    task_name = "task_check_concept_decision"
    description = "Nakijken besluit"

    @staticmethod
    def get_steps():
        return [
            *CreateConceptDecision.get_steps(),
            __class__(),
        ]


class Decision(AbstractUserTask):
    endpoint = "decisions"
    event = events.DecisionEvent
    task_name = "task_create_decision"
    description = "Verwerken definitieve besluit"

    def __init__(self, type=DecisionType.HolidayRental.NO_DECISION):
        data = {"decision_type": type}
        super(Decision, self).__init__(**data)

    @staticmethod
    def get_steps(type=DecisionType.HolidayRental.NO_DECISION):
        return [
            *CheckConceptDecision.get_steps(),
            __class__(type=type),
        ]

    def get_post_data(self, case, task):
        return {
            "case": case.data["id"],
            "camunda_task_id": task["camunda_task_id"],
        }


class SendTaxCollection(GenericUserTask):
    task_name = "task_send_tax_collection"
    description = "Versturen invordering belastingen"

    @staticmethod
    def get_steps():
        return [*Decision.get_steps(type=DecisionType.HolidayRental.FINE), __class__()]


class PlanNextStep(GenericUserTask):
    asynchronous = True
    task_name = "task_set_next_step"
    description = "Uitzetten vervolgstap"

    def __init__(self, next_step=NextStep.CLOSE):
        data = {"next_step": {"value": next_step}}
        super(PlanNextStep, self).__init__(**data)

    @staticmethod
    def get_steps():
        return [*SendTaxCollection.get_steps(), __class__(next_step=NextStep.CLOSE)]


class MonitorReopeningRequest(GenericUserTask):
    # task_name = "task_monitor_reopening_request"
    task_name = "Activity_0wienly"  # BUG in Spiff, should be renamed
    description = "Monitoren heropeningsverzoek"

    @staticmethod
    def get_steps():
        return [
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.CLOSURE),
            __class__(),
        ]


class ContactOwner(GenericUserTask):
    # task_name = "task_contact_owner"
    task_name = "Activity_0gjczg7"  # BUG in Spiff, should be renamed
    description = "Contacteren eigenaar"

    @staticmethod
    def get_steps():
        return [*MonitorReopeningRequest.get_steps(), WaitForTimer(), __class__()]


class JudgeReopeningRequest(GenericUserTask):
    # task_name = "task_judge_reopening_request"
    task_name = "Activity_0fp5tdz"  # BUG in Spiff, should be renamed
    description = "Beoordelen heropeningsverzoek"

    def __init__(self, review_request=ReviewRequest.ACCEPTED):
        data = {"beoordeling_verzoek": {"value": review_request}}

        super(JudgeReopeningRequest, self).__init__(**data)

    @staticmethod
    def get_steps(review_request=ReviewRequest.ACCEPTED):
        return [
            *SaveFireBrigadeAdvice.get_steps(),
            __class__(review_request=review_request),
        ]


class SaveFireBrigadeAdvice(GenericUserTask):
    # task_name = "task_save_fireman_advice"
    task_name = "Activity_19r9rzm"  # BUG in Spiff, should be renamed
    description = "Opslaan brandweeradvies"

    @staticmethod
    def get_steps():
        return [
            *ProcessNotice.get_steps(type=SummonTypes.HolidayRental.CLOSURE),
            __class__(),
        ]


class MonitorReopeningRequestToBeDelivered(GenericUserTask):
    # task_name = "task_monitor_new_reopening_request"
    task_name = "Activity_0zh0d0s"  # BUG in Spiff, should be renamed
    description = "Monitoren nieuw aan te leveren heropeningsverzoek"

    @staticmethod
    def get_steps():
        return [
            *JudgeReopeningRequest.get_steps(review_request=ReviewRequest.DECLINED),
            __class__(),
        ]


class Reopen(GenericUserTask):
    # task_name = "task_reopening"
    task_name = "Activity_1fovs3d"  # BUG in Spiff, should be renamed
    description = "Heropenen"

    @staticmethod
    def get_steps():
        return [*JudgeReopeningRequest.get_steps(), __class__()]


class ScheduleRecheck(GenericUserTask):
    # task_name = "task_schedule_recheck"
    task_name = "Activity_1tmqvpn"  # BUG in Spiff, should be renamed
    description = "Uitzetten hercontrole"

    @staticmethod
    def get_steps():
        return [*Reopen.get_steps(), __class__()]


class ContactDistrict(GenericUserTask):
    task_name = "task_contact_city_district"
    description = "Contacteren stadsdeel"

    @staticmethod
    def get_steps():
        return [
            *Decision.get_steps(type=DecisionType.HolidayRental.REVOKE_VV_PERMIT),
            __class__(),
        ]


class RequestAuthorization(GenericUserTask):
    task_name = "task_request_authorization"
    description = "Aanvragen machtiging"

    @staticmethod
    def get_steps():
        return [
            *Debrief.get_steps(violation=Violation.ADDITIONAL_VISIT_WITH_AUTHORIZATION),
            __class__(),
        ]


class MonitorIncomingAuthorization(GenericUserTask):
    task_name = "task_monitor_incoming_authorization"
    description = "Monitoren binnenkomen machtiging"

    @staticmethod
    def get_steps():
        return [*RequestAuthorization.get_steps(), __class__()]


class Close(AbstractUserTask):
    event = events.CloseEvent
    endpoint = "case-close"
    task_name = "task_close_case"
    description = "Afsluiten zaak"

    def __init__(
        self, reason=CloseReason.HolidayRental.NO_FROUD, description="Some description"
    ):
        super(Close, self).__init__(reason=reason, description=description)

    def get_post_data(self, case, task):
        return {
            "case": case.data["id"],
            "theme": case.data["theme"],
            "case_user_task_id": task["case_user_task_id"],
        }

    @staticmethod
    def get_steps():
        return [*PlanNextStep.get_steps(), __class__()]
