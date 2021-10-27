import logging

from api import events
from api.config import DecisionType, Objection
from api.tasks import AbstractUserTask, GenericUserTask
from api.tasks.summon import JudgeView

logger = logging.getLogger("api")


class CreateConceptDecision(GenericUserTask):
    asynchronous = True
    task_name = "task_make_concept_decision"
    description = "Opstellen concept besluit"

    @staticmethod
    def get_steps(objection_valid=Objection.NO):
        return [
            *JudgeView.get_steps(objection_valid=objection_valid),
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
        return super().get_post_data(case, task) | {
            "case_user_task_id": task["case_user_task_id"],
        }


class SendTaxCollection(GenericUserTask):
    task_name = "task_send_tax_collection"
    description = "Versturen invordering belastingen"

    @staticmethod
    def get_steps():
        return [*Decision.get_steps(type=DecisionType.HolidayRental.FINE), __class__()]


class ContactDistrict(GenericUserTask):
    task_name = "task_contact_city_district"
    description = "Contacteren stadsdeel"

    @staticmethod
    def get_steps():
        return [
            *Decision.get_steps(type=DecisionType.HolidayRental.REVOKE_VV_PERMIT),
            __class__(),
        ]
