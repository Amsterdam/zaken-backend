import logging

from api import events
from api.config import Violation
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.visit import test_doorgeven_status_top
from api.user_tasks import (
    task_afwachten_intern_onderzoek,
    task_create_debrief,
    task_opstellen_beeldverslag,
    task_opstellen_rapport_van_bevindingen,
    task_opstellen_verkorte_rapportage_huisbezoek,
    task_terugkoppelen_melder_1,
    task_terugkoppelen_melder_2,
)

logger = logging.getLogger(__name__)


class test_create_debrief(AbstractUserTask, task_create_debrief):
    event = events.DebriefingEvent
    endpoint = "debriefings"

    def __init__(self, violation=Violation.NO, feedback="Some feedback"):
        super(test_create_debrief, self).__init__(
            violation=violation, feedback=feedback
        )

    @staticmethod
    def get_steps(violation=Violation.NO):
        return [*test_doorgeven_status_top.get_steps(), __class__(violation=violation)]

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "case_user_task_id": task["case_user_task_id"],
        }


class test_terugkoppelen_melder_1(GenericUserTask, task_terugkoppelen_melder_1):
    @staticmethod
    def get_steps():
        return [*test_create_debrief.get_steps(violation=Violation.NO), __class__()]


class test_terugkoppelen_melder_2(GenericUserTask, task_terugkoppelen_melder_2):
    @staticmethod
    def get_steps():
        return [*test_create_debrief.get_steps(violation=Violation.YES), __class__()]


class test_afwachten_intern_onderzoek(GenericUserTask, task_afwachten_intern_onderzoek):
    @staticmethod
    def get_steps():
        return [
            *test_create_debrief.get_steps(
                violation=Violation.ADDITIONAL_RESEARCH_REQUIRED
            ),
            __class__(),
        ]


class test_opstellen_beeldverslag(GenericUserTask, task_opstellen_beeldverslag):
    @staticmethod
    def get_steps():
        return [*test_create_debrief.get_steps(violation=Violation.YES), __class__()]


class test_opstellen_rapport_van_bevindingen(
    GenericUserTask, task_opstellen_rapport_van_bevindingen
):
    @staticmethod
    def get_steps():
        return [*test_create_debrief.get_steps(violation=Violation.YES), __class__()]


class test_opstellen_verkorte_rapportage_huisbezoek(
    GenericUserTask, task_opstellen_verkorte_rapportage_huisbezoek
):
    @staticmethod
    def get_steps():
        return [*test_create_debrief.get_steps(violation=Violation.NO), __class__()]
