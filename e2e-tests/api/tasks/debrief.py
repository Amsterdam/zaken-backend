import logging

from api import events
from api.config import Violation
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.visit import Visit

logger = logging.getLogger("api")


class Debrief(AbstractUserTask):
    event = events.DebriefingEvent
    endpoint = "debriefings"
    task_name = "task_create_debrief"
    description = "Verwerken debrief"
    asynchronous = True

    def __init__(self, violation=Violation.NO, feedback="Some feedback"):
        super(Debrief, self).__init__(violation=violation, feedback=feedback)

    @staticmethod
    def get_steps(violation=Violation.NO):
        return [*Visit.get_steps(), __class__(violation=violation)]

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "case_user_task_id": task["case_user_task_id"],
        }


class InternalResearch(GenericUserTask):
    task_name = "task_internal_reasearch"
    description = "Afwachten intern onderzoek"

    @staticmethod
    def get_steps():
        return [
            *Debrief.get_steps(violation=Violation.ADDITIONAL_RESEARCH_REQUIRED),
            __class__(),
        ]


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
