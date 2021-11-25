import logging

from api import events
from api.config import DecisionType, ObjectionValid
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.summon import test_beoordelen_zienswijze
from api.user_tasks import (
    task_contacteren_stadsdeel,
    task_nakijken_besluit,
    task_opstellen_concept_besluit,
    task_versturen_invordering_belastingen,
    task_verwerken_definitieve_besluit,
)

logger = logging.getLogger(__name__)


class test_opstellen_concept_besluit(GenericUserTask, task_opstellen_concept_besluit):
    @staticmethod
    def get_steps(objection_valid=ObjectionValid.NO):
        return [
            *test_beoordelen_zienswijze.get_steps(objection_valid=objection_valid),
            __class__(),
        ]


class test_nakijken_besluit(GenericUserTask, task_nakijken_besluit):
    @staticmethod
    def get_steps():
        return [
            *test_opstellen_concept_besluit.get_steps(),
            __class__(),
        ]


class test_verwerken_definitieve_besluit(
    AbstractUserTask, task_verwerken_definitieve_besluit
):
    endpoint = "decisions"
    event = events.DecisionEvent

    def __init__(self, type=DecisionType.HolidayRental.NO_DECISION):
        data = {"decision_type": type}
        super(test_verwerken_definitieve_besluit, self).__init__(**data)

    @staticmethod
    def get_steps(type=DecisionType.HolidayRental.NO_DECISION):
        return [
            *test_nakijken_besluit.get_steps(),
            __class__(type=type),
        ]

    def get_post_data(self, case, task):
        return super().get_post_data(case, task) | {
            "case_user_task_id": task["case_user_task_id"],
        }


class test_versturen_invordering_belastingen(
    GenericUserTask, task_versturen_invordering_belastingen
):
    @staticmethod
    def get_steps():
        return [
            *test_verwerken_definitieve_besluit.get_steps(
                type=DecisionType.HolidayRental.FINE
            ),
            __class__(),
        ]


class test_contacteren_stadsdeel(GenericUserTask, task_contacteren_stadsdeel):
    @staticmethod
    def get_steps():
        return [
            *test_verwerken_definitieve_besluit.get_steps(
                type=DecisionType.HolidayRental.REVOKE_VV_PERMIT
            ),
            __class__(),
        ]
